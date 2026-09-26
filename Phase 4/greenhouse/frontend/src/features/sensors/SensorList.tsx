import { useEffect, useState } from 'react'
import { createSensor, fetchSensors, type SensorDto } from '../../services/api'

type SensorType = 'moisture' | 'light'

function readableType(deviceType: string) {
  return deviceType.replaceAll('_', ' ')
}

export default function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState<SensorType | null>(null)
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

  const addSensor = async (type: SensorType) => {
    try {
      setCreating(type)
      setError(null)
      const created = await createSensor(type)
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
            Moisture and light sensors are created through Factory Method and saved in PostgreSQL.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void addSensor('moisture')}
            disabled={creating !== null}
            className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {creating === 'moisture' ? 'Adding…' : 'Add moisture'}
          </button>
          <button
            type="button"
            onClick={() => void addSensor('light')}
            disabled={creating !== null}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {creating === 'light' ? 'Adding…' : 'Add light'}
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
            <div key={sensor.id} className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h4 className="font-medium text-slate-900">{sensor.display_name}</h4>
                  <p className="mt-1 text-sm capitalize text-slate-500">
                    {readableType(sensor.device_type)}
                  </p>
                </div>
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
                  sensor
                </span>
              </div>

              <dl className="mt-4 space-y-2 text-sm">
                {Object.entries(sensor.default_config).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-4 border-t border-slate-200 pt-2">
                    <dt className="text-slate-500">{key.replaceAll('_', ' ')}</dt>
                    <dd className="text-right font-medium text-slate-700">{String(value)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      )}

      <span className="mt-4 inline-block rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        Phase 2 — Factory Method
      </span>
    </article>
  )
}
