import { Link } from 'react-router-dom'

/** Landing page describing what the Phase 1 skeleton contains. */
export default function HomePage() {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
      <h2 className="text-2xl font-bold text-slate-900">Smart Greenhouse control system</h2>
      <p className="mt-3 max-w-2xl text-slate-600">
        Phase 1 skeleton: a running three-tier stack with a FastAPI backend, a PostgreSQL
        database managed by Alembic migrations, and this React + TypeScript frontend. No
        greenhouse business logic yet — later phases fill the dashboard sections.
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
