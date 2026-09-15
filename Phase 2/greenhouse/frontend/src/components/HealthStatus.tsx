import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from '../services/api'

type State =
  | { kind: 'loading' }
  | { kind: 'loaded'; health: HealthResponse }
  | { kind: 'error' }

/** Badge in the header showing whether the API and the database are reachable. */
export default function HealthStatus() {
  const [state, setState] = useState<State>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const health = await fetchHealth()
        if (!cancelled) setState({ kind: 'loaded', health })
      } catch {
        if (!cancelled) setState({ kind: 'error' })
      }
    }

    load()
    const timer = setInterval(load, 15000) // refresh every 15 s

    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  if (state.kind === 'loading') {
    return <span className={badge('slate')}>Checking…</span>
  }

  if (state.kind === 'error') {
    return <span className={badge('red')}>API: unreachable</span>
  }

  const { status, db } = state.health
  const tone = status === 'ok' && db === 'ok' ? 'emerald' : 'amber'

  return (
    <span className={badge(tone)}>
      API: {status} · DB: {db}
    </span>
  )
}

/** Tailwind classes for each status colour. */
function badge(tone: 'emerald' | 'amber' | 'red' | 'slate') {
  const tones = {
    emerald: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
    amber: 'bg-amber-50 text-amber-700 ring-amber-200',
    red: 'bg-red-50 text-red-700 ring-red-200',
    slate: 'bg-slate-100 text-slate-600 ring-slate-200',
  }
  return `inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ring-1 ${tones[tone]}`
}
