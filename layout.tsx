import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'InvestGPT AI — Valuation Suite',
  description: 'DCF calculator and discount-rate tools',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="sticky top-0 bg-white/70 backdrop-blur border-b">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
            <a className="font-semibold" href="/">InvestGPT AI</a>
            <nav className="text-sm flex gap-4">
              <a href="/dcf" className="hover:underline">DCF</a>
              <a href="/discount-rate" className="hover:underline">Discount Rate</a>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  )
}