import { useEffect, useState } from 'react'
import {
  createSensor,
  fetchSensors,
  type SensorAdapter,
  type SensorDto,
} from '../../services/api'
import SensorCard from './SensorCard'

type SensorType = 'moisture' | 'light'

export default function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const result = await fetchSensors()
        if (!cancelled) setSensors(result)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Could not load sensors')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  const addSensor = async (type: SensorType, adapter: SensorAdapter = 'simulation') => {
    try {
      setCreating(`${adapter}-${type}`)
      setError(null)
      const created = await createSensor(type, adapter)
      setSensors((current) => [created, ...current])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create sensor')
    } finally {
      setCreating(null)
    }
  }

  return (
    <article
      id="sensors"
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm sm:col-span-2 lg:col-span-3"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Sensors</h3>
          <p className="mt-2 text-sm text-slate-600">
            Each sensor is read through an adapter. Readings are stored in PostgreSQL and the
            cards refresh from the stored history every few seconds (temporary poll until the
            Phase 12 WebSocket).
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void addSensor('moisture')}
            disabled={creating !== null}
            className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {creating === 'simulation-moisture' ? 'Adding…' : 'Add moisture'}
          </button>
          <button
            type="button"
            onClick={() => void addSensor('light')}
            disabled={creating !== null}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {creating === 'simulation-light' ? 'Adding…' : 'Add light'}
          </button>
          <button
            type="button"
            onClick={() => void addSensor('moisture', 'vendor')}
            disabled={creating !== null}
            title="Moisture sensor read through the vendor stub adapter"
            className="rounded-md border border-amber-300 bg-white px-3 py-2 text-sm font-medium text-amber-700 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {creating === 'vendor-moisture' ? 'Adding…' : 'Add vendor moisture'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <p className="mt-5 text-sm text-slate-500">Loading sensors…</p>
      ) : sensors.length === 0 ? (
        <p className="mt-5 rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          No sensors yet. Add a moisture or light sensor to create the first one.
        </p>
      ) : (
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {sensors.map((sensor) => (
            <SensorCard key={sensor.id} sensor={sensor} />
          ))}
        </div>
      )}

      <span className="mt-4 inline-block rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        Phase 5 — Adapter
      </span>
    </article>
  )
}
