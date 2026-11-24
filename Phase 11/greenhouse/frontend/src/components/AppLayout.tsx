import { NavLink, Outlet } from 'react-router-dom'
import HealthStatus from './HealthStatus'

/** Shared page frame: header with title, navigation and health badge. */
export default function AppLayout() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3 py-1.5 text-sm font-medium transition ${
      isActive ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:bg-slate-100'
    }`

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-6 py-4">
          <h1 className="text-xl font-bold text-emerald-600">Smart Greenhouse</h1>
          <nav className="flex gap-1">
            <NavLink to="/" end className={linkClass}>
              Home
            </NavLink>
            <NavLink to="/dashboard" className={linkClass}>
              Dashboard
            </NavLink>
          </nav>
          <div className="ml-auto">
            <HealthStatus />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}
