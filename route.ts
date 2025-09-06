import { NextResponse } from "next/server";

type DCFIn = {
  ticker: string;
  model?: "fcff" | "equity";
  shares_out: number;
  fcf_base: number;
  fcf_growth?: number | number[];
  discount_rate: number;
  terminal_growth: number;
  years?: number;
  net_debt?: number;
};

function seqGrowth(base:number, g:number|number[], n:number){
  const gs = Array.isArray(g) ? [...g, ...Array(Math.max(0, n - g.length)).fill(g.at(-1))] : Array(n).fill(g);
  const vals:number[] = [];
  let f = base;
  for (let i=0;i<n;i++){
    f = i>0 ? f*(1+gs[i]) : base*(1+gs[i]);
    vals.push(f);
  }
  return vals;
}

export async function POST(req: Request) {
  const x = (await req.json()) as DCFIn;
  const r = x.discount_rate, g = x.terminal_growth;
  const years = x.years ?? 5;
  const model = x.model ?? "fcff";
  const netDebt = x.net_debt ?? 0;

  if (r <= g) return NextResponse.json({error:"Discount rate must exceed terminal growth"}, {status:400});

  const fcfSeries = seqGrowth(x.fcf_base, x.fcf_growth ?? 0.07, years);
  const pv_cf = fcfSeries.reduce((acc, v, i) => acc + v / Math.pow(1+r, i+1), 0);
  const tv = fcfSeries.at(-1)! * (1+g) / (r-g);
  const pv_tv = tv / Math.pow(1+r, years);
  const present_value = pv_cf + pv_tv;
  const equity_value = model === "equity" ? present_value : present_value - netDebt;
  const per_share = equity_value / x.shares_out;

  return NextResponse.json({ pv_cashflows: pv_cf, pv_terminal: pv_tv, present_value, equity_value, per_share, assumptions_echo: x});
}
