export default function Home() {
  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-2">Valuation Tools</h1>
      <p className="text-gray-600 mb-6">Quick links to DCF and discount-rate helpers.</p>
      <div className="grid sm:grid-cols-2 gap-4">
        <a href="/dcf" className="bg-white border rounded-2xl p-4 hover:shadow">
          <div className="font-semibold mb-1">DCF Value Calculator</div>
          <div className="text-sm text-gray-600">Forecast FCF, discount, and compute per-share value.</div>
        </a>
        <a href="/discount-rate" className="bg-white border rounded-2xl p-4 hover:shadow">
          <div className="font-semibold mb-1">Discount Rate (WACC/CAPM)</div>
          <div className="text-sm text-gray-600">Compute cost of equity and WACC from inputs.</div>
        </a>
      </div>
    </main>
  )
}