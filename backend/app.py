from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from dcf_engine import dcf_two_stage_fade
from data_fetchers import get_company_facts_cached, build_financials_hybrid, yahoo_5y_growth_estimate

app = FastAPI(title="InvestGPT API", version="1.0.0")

# CORS: allow your local dev and GitHub Pages origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://dannycap.github.io",
    "https://dannycap.github.io/test1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DCFRequest(BaseModel):
    ticker: str
    years: int = 5
    growth: float = 0.08
    fade_years: int = 2
    wacc: float = 0.10
    terminal_growth: float = 0.025
    start_year: int = 2015
    use_yahoo_growth: bool = True
    override_cash: Optional[float] = None
    override_debt: Optional[float] = None

class DCFResponse(BaseModel):
    ticker: str
    kpis: Dict[str, Any]
    projection: List[Dict[str, Any]]
    financials: Dict[str, Any]
    statements: Dict[str, Any]
    sensitivity: Optional[Dict[str, Any]] = None
    footnotes: List[str]

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "InvestGPT API"}

@app.post("/api/dcf", response_model=DCFResponse)
async def calculate_dcf(request: DCFRequest):
    try:
        # Fetch company data
        facts = get_company_facts_cached(request.ticker)
        fins = build_financials_hybrid(facts, request.ticker, start_year=request.start_year)

        # Validate FCF
        if fins.empty or "FCF" not in fins.columns or fins["FCF"].dropna().empty:
            raise HTTPException(status_code=400, detail="Insufficient FCF data for DCF calculation")

        last_row = fins.dropna(subset=["FCF"]).iloc[-1]
        last_fcf = float(last_row["FCF"]) if pd.notna(last_row["FCF"]) else 0.0

        # Cash & Debt
        cash_series = fins.get("Cash", pd.Series(dtype=float)).dropna()
        debt_series = fins.get("Debt", pd.Series(dtype=float)).dropna()
        cash_val = request.override_cash if request.override_cash is not None else (float(cash_series.iloc[-1]) if not cash_series.empty else 0.0)
        debt_val = request.override_debt if request.override_debt is not None else (float(debt_series.iloc[-1]) if not debt_series.empty else 0.0)

        shares_val = fins.attrs.get("shares_outstanding_scalar", None)

        # Growth handling
        footnotes: List[str] = []
        g1 = request.growth
        if request.use_yahoo_growth:
            yahoo_growth = yahoo_5y_growth_estimate(request.ticker)
            if yahoo_growth is not None:
                g1 = float(yahoo_growth)
                footnotes.append(f"Using Yahoo Finance 5y growth estimate: {g1:.2%}")

        # DCF core
        ev, pv_fcfs, pv_tv, fcfs, growths = dcf_two_stage_fade(
            last_fcf, request.years, g1, request.wacc, request.terminal_growth, request.fade_years
        )

        equity_value = ev + cash_val - debt_val
        price_per_share = equity_value / shares_val if shares_val and shares_val > 0 else None

        kpis = {
            "last_fcf": last_fcf,
            "cash": cash_val,
            "debt": debt_val,
            "enterprise_value": ev,
            "equity_value": equity_value,
            "shares_outstanding": shares_val,
            "price_per_share": price_per_share,
            "terminal_value_pv": pv_tv,
            "wacc": request.wacc,
            "terminal_growth": request.terminal_growth,
            "stage1_growth": g1,
        }

        projection = [
            {
                "year": i + 1,
                "growth_rate": float(growths[i]) if i < len(growths) else 0.0,
                "fcf": float(fcfs[i]) if i < len(fcfs) else 0.0,
                "pv_fcf": float(pv_fcfs[i]) if i < len(pv_fcfs) else 0.0,
            }
            for i in range(request.years)
        ]

        financials_dict = fins.to_dict(orient="records")

        sensitivity = None
        if shares_val and shares_val > 0:
            sensitivity = calculate_sensitivity(
                last_fcf, request.years, g1, request.wacc, request.terminal_growth,
                request.fade_years, cash_val, debt_val, shares_val
            )

        return DCFResponse(
            ticker=request.ticker,
            kpis=kpis,
            projection=projection,
            financials={"data": financials_dict, "columns": list(fins.columns)},
            statements={},
            sensitivity=sensitivity,
            footnotes=footnotes,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def calculate_sensitivity(last_fcf, years, g1, wacc, tgr, fade_years, cash, debt, shares):
    wacc_range = np.linspace(max(0.05, wacc - 0.03), min(0.20, wacc + 0.03), 7)
    tgr_range = np.linspace(max(0.0, tgr - 0.01), min(0.05, tgr + 0.01), 5)
    results: Dict[str, Any] = {}
    for w in wacc_range:
        for t in tgr_range:
            try:
                ev, _, _, _, _ = dcf_two_stage_fade(last_fcf, years, g1, float(w), float(t), fade_years)
                eq = ev + cash - debt
                price = eq / shares
                results[f"wacc_{w:.3f}_tgr_{t:.3f}"] = price
            except Exception:
                results[f"wacc_{w:.3f}_tgr_{t:.3f}"] = None
    return {"wacc_values": wacc_range.tolist(), "tgr_values": tgr_range.tolist(), "grid": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
