import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Network, Shield } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import ApplicationDetail from './pages/ApplicationDetail'
import FraudGraph from './pages/FraudGraph'

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation()
  const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to))
  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        active ? 'bg-blue-700 text-white' : 'text-blue-100 hover:bg-blue-700/60'
      }`}
    >
      {children}
    </Link>
  )
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-screen-2xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-7 h-7 text-blue-300" />
            <span className="text-xl font-bold tracking-tight">DeepAudit</span>
            <span className="text-blue-400 text-sm font-normal hidden sm:block">
              Government Benefits Fraud Detection
            </span>
          </div>
          <nav className="flex items-center gap-1">
            <NavLink to="/">
              <LayoutDashboard className="w-4 h-4" /> Dashboard
            </NavLink>
            <NavLink to="/graph">
              <Network className="w-4 h-4" /> Fraud Graph
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-screen-2xl mx-auto w-full px-6 py-6">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><Dashboard /></Layout>} />
        <Route path="/applications/:id" element={<Layout><ApplicationDetail /></Layout>} />
        <Route path="/graph" element={<Layout><FraudGraph /></Layout>} />
      </Routes>
    </BrowserRouter>
  )
}
