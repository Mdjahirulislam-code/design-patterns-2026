import { useCallback, useEffect, useState } from 'react'
import {
  fetchLocations,
  fetchOverview,
  type LocationOverviewDto,
  type LocationSummaryDto,
  type OverviewReadingDto,
  type OverviewZoneDto,
} from '../../services/api'

function errorText(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback
}

function readable(text: string) {
  return text.replaceAll('_', ' ')
}

function formatValue(reading: OverviewReadingDto) {
  const digits = reading.unit === 'lux' ? 0 : 2
  return `${reading.value.toFixed(digits)} ${reading.unit}`
}

function StatCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-2">{children}</div>
    </div>
  )
}

function EmptyText({ children }: { children: React.ReactNode }) {
  return <p className="text-sm text-slate-500">{children}</p>
}

function ZoneCard({ zone }: { zone: OverviewZoneDto }) {
  const readings = new Map(zone.latest_readings.map((r) => [r.device_id, r]))

  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h4 className="font-medium text-slate-900">{zone.name}</h4>
        <span className="text-xs text-slate-500">
          Moisture band {zone.moisture_threshold_low.toFixed(2)}–
          {zone.moisture_threshold_high.toFixed(2)}
        </span>
      </div>

      {zone.devices.length === 0 ? (
        <p className="mt-3 rounded-md border border-dashed border-slate-300 p-3 text-sm text-slate-500">
          No devices assigned to this zone.
        </p>
      ) : (
        <ul className="mt-3 space-y-2">
          {zone.devices.map((device) => {
            const reading = readings.get(device.id)
            return (
              <li key={device.id} className="rounded-md bg-slate-50 p-3 text-sm">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium text-slate-800">{device.display_name}</span>
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
                    {device.role}
                  </span>
                </div>
                <p className="mt-1 text-xs capitalize text-slate-500">{readable(device.device_type)}</p>

                {reading ? (
                  <p className="mt-2 text-slate-700">
                    <span className="font-semibold text-slate-900">{formatValue(reading)}</span>
                    <span className="text-xs text-slate-500">
                      {' '}
                      · {new Date(reading.recorded_at).toLocaleTimeString()} · tracking{' '}
                      {reading.tracking_enabled ? 'on' : 'off'} · every{' '}
                      {reading.sampling_interval_seconds} s
                    </span>
                  </p>
                ) : (
                  <p className="mt-2 text-xs text-slate-500">No reading stored yet.</p>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

/** Phase 7 — Facade: the whole location snapshot comes from ONE overview request. */
export default function OverviewPanel() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [locationId, setLocationId] = useState('')
  const [overview, setOverview] = useState<LocationOverviewDto | null>(null)
  const [loadingLocations, setLoadingLocations] = useState(true)
  const [loadingOverview, setLoadingOverview] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // The only call that fills the cards. Used on select and on Refresh.
  const loadOverview = useCallback(async (id: string) => {
    if (!id) return
    try {
      setLoadingOverview(true)
      setError(null)
      setOverview(await fetchOverview(id))
    } catch (err) {
      setOverview(null)
      setError(errorText(err, 'Could not load the overview'))
    } finally {
      setLoadingOverview(false)
    }
  }, [])

  // Location list for the dropdown, then the overview of the first location
  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const list = await fetchLocations()
        if (cancelled) return
        setLocations(list)
        if (list.length > 0) {
          setLocationId(list[0].id)
          void loadOverview(list[0].id)
        }
      } catch (err) {
        if (!cancelled) setError(errorText(err, 'Could not load locations'))
      } finally {
        if (!cancelled) setLoadingLocations(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [loadOverview])

  const selectLocation = (id: string) => {
    setLocationId(id)
    void loadOverview(id)
  }

  return (
    <article id="overview" className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Overview</h3>
          <p className="mt-2 text-sm text-slate-600">
            The state of one location at a glance: assigned devices, latest readings per zone,
            the saved strategy and its current recommendation.
          </p>
        </div>

        {locations.length > 0 && (
          <div className="flex flex-wrap items-end gap-2">
            <label className="text-sm text-slate-600">
              <span className="block text-xs uppercase tracking-wide text-slate-500">Location</span>
              <select
                value={locationId}
                onChange={(event) => selectLocation(event.target.value)}
                disabled={loadingOverview}
                className="mt-1 rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-900 disabled:opacity-50"
              >
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={() => void loadOverview(locationId)}
              disabled={loadingOverview || !locationId}
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loadingOverview ? 'Loading…' : 'Refresh'}
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      {loadingLocations ? (
        <p className="mt-5 text-sm text-slate-500">Loading…</p>
      ) : locations.length === 0 ? (
        <p className="mt-5 rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          No locations yet. Create one with <code>POST /api/locations/config</code> (see
          location.json).
        </p>
      ) : !overview ? (
        loadingOverview && <p className="mt-5 text-sm text-slate-500">Loading overview…</p>
      ) : (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Sensors">
              <p className="text-2xl font-semibold text-slate-900">{overview.device_counts.sensor}</p>
              <p className="text-xs text-slate-500">assigned to zones</p>
            </StatCard>

            <StatCard label="Actuators">
              <p className="text-2xl font-semibold text-slate-900">{overview.device_counts.actuator}</p>
              <p className="text-xs text-slate-500">assigned to zones</p>
            </StatCard>

            <StatCard label="Strategy">
              {overview.strategy_key ? (
                <p className="text-lg font-semibold capitalize text-slate-900">{overview.strategy_key}</p>
              ) : (
                <EmptyText>No strategy saved for this location.</EmptyText>
              )}
            </StatCard>

            <StatCard label="Recommendation">
              {overview.last_recommendation ? (
                <>
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${
                      overview.last_recommendation.action === 'irrigate'
                        ? 'bg-sky-50 text-sky-700 ring-sky-200'
                        : 'bg-slate-100 text-slate-700 ring-slate-200'
                    }`}
                  >
                    {overview.last_recommendation.action}
                  </span>
                  <p className="mt-2 text-sm text-slate-700">{overview.last_recommendation.reason}</p>
                </>
              ) : (
                <EmptyText>No recommendation. Save a strategy first.</EmptyText>
              )}
            </StatCard>
          </div>

          <h4 className="mt-6 text-sm font-semibold text-slate-700">
            Zones in {overview.location.name}
          </h4>

          {overview.zones.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">This location has no zones.</p>
          ) : (
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {overview.zones.map((zone) => (
                <ZoneCard key={zone.id} zone={zone} />
              ))}
            </div>
          )}
        </>
      )}

      <span className="mt-4 inline-block rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        Phase 7 — Facade
      </span>
    </article>
  )
}
