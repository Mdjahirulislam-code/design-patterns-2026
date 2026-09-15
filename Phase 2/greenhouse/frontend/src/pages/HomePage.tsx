import { Link } from 'react-router-dom'

/** Landing page describing the current project phase. */
export default function HomePage() {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
      <h2 className="text-2xl font-bold text-slate-900">Smart Greenhouse control system</h2>
      <p className="mt-3 max-w-2xl text-slate-600">
        Phase 2 builds on the running three-tier skeleton. Moisture and light sensors are now created
        through Factory Method, stored in PostgreSQL, and shown in the dashboard.
      </p>
      <Link
        to="/dashboard"
        className="mt-6 inline-block rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        Open dashboard
      </Link>
    </section>
  )
}
