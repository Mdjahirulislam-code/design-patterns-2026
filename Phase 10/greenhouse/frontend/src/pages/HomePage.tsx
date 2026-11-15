import { Link } from 'react-router-dom'

/** Landing page describing the current project phase. */
export default function HomePage() {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
      <h2 className="text-2xl font-bold text-slate-900">Smart Greenhouse control system</h2>
      <p className="mt-3 max-w-2xl text-slate-600">
        Phase 10 adds the Command pattern. Start pump, stop pump and set light level are command
        objects that check the actuator state, run through the decorated port and are stored in a
        command history.
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
