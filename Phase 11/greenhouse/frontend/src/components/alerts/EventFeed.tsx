import { useCallback, useEffect, useState } from 'react'
import {
  fetchAlerts,
  fetchLocationZones,
  fetchLocations,
  type AlertDto,
  type AlertSeverity,
  type LocationSummaryDto,
  type LocationZoneDto,
} from '../../services/api'

// Phase 11 polls the API. Phase 12 adds the WebSocket in services/realtime.ts.
const POLL_INTERVAL_MS = 5000

const SEVERITY_BADGE: Record<AlertSeverity, string> = {
  info: 'bg-sky-50 text-sky-700 ring-sky-200',
  warning: 'bg-amber-50 text-amber-700 ring-amber-200',
  critical: 'bg-red-50 text-red-700 ring-red-200',
}

function errorText(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback
}

/** Phase 11 — Observer: alerts stored by the subscribers, newest first. */
export default function EventFeed() {
  const [alerts, setAlerts] = useState<AlertDto[]>([])
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [zones, setZones] = useState<LocationZoneDto[]>([])
  const [locationId, setLocationId] = useState('')
  const [zoneId, setZoneId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastPoll, setLastPoll] = useState<Date | null>(null)

  // location list for the filter
  useEffect(() => {
    fetchLocations()
      .then(setLocations)
      .catch(() => setLocations([]))
  }, [])

  // zones of the chosen location
  useEffect(() => {
    setZoneId('')
    if (!locationId) {
      setZones([])
      return
    }
    fetchLocationZones(locationId)
      .then(setZones)
      .catch(() => setZones([]))
  }, [locationId])

  const load = useCallback(async () => {
    try {
      const rows = await fetchAlerts({
        locationId: locationId || undefined,
        zoneId: zoneId || undefined,
      })
      setAlerts(rows)
      setError(null)
      setLastPoll(new Date())
    } catch (err) {
      setError(errorText(err, 'Could not load alerts'))
    } finally {
      setLoading(false)
    }
  }, [locationId, zoneId])

  // poll every 5 seconds (and right away when the filter changes)
  useEffect(() => {
    void load()
    const timer = window.setInterval(() => void load(), POLL_INTERVAL_MS)
    return () => window.clearInterval(timer)
  }, [load])

  const zoneName = (id: string | null) => zones.find((zone) => zone.id === id)?.name

  return (
    <article id="events" className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Events</h3>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Active alerts created by the event subscribers: moisture below a zone's low
            threshold, failed commands, and actuators that entered error. The list is stored in
            the database and refreshes every 5 seconds.
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-2">
          <label className="text-sm text-slate-600">
            <span className="block text-xs uppercase tracking-wide text-slate-500">Location</span>
            <select
              value={locationId}
              onChange={(event) => setLocationId(event.target.value)}
              className="mt-1 rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-900"
            >
              <option value="">All locations</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {location.name}
                </option>
              ))}
            </select>
          </label>

          <label className="text-sm text-slate-600">
            <span className="block text-xs uppercase tracking-wide text-slate-500">Zone</span>
            <select
              value={zoneId}
              onChange={(event) => setZoneId(event.target.value)}
              disabled={!locationId}
              className="mt-1 rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-900 disabled:opacity-50"
            >
              <option value="">All zones</option>
              {zones.map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {zone.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <p className="mt-5 text-sm text-slate-500">Loading alerts…</p>
      ) : alerts.length === 0 ? (
        <p className="mt-5 rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          No active alerts{locationId ? ' for this filter' : ''}.
        </p>
      ) : (
        <ul className="mt-5 space-y-2">
          {alerts.map((alert) => (
            <li
              key={alert.id}
              className="flex flex-wrap items-start justify-between gap-3 rounded-md border border-slate-200 bg-slate-50 p-3"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${SEVERITY_BADGE[alert.severity] ?? SEVERITY_BADGE.info}`}
                  >
                    {alert.severity}
                  </span>
                  <span className="text-sm font-medium text-slate-900">{alert.message}</span>
                </div>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  {alert.event_type}
                  {alert.zone_id
                    ? ` · zone ${zoneName(alert.zone_id) ?? alert.zone_id.slice(0, 8)}`
                    : ' · no zone'}
                  {alert.device_id ? ` · device ${alert.device_id.slice(0, 8)}` : ''}
                </p>
              </div>
              <span className="whitespace-nowrap text-xs text-slate-500">
                {new Date(alert.created_at).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}

      <p className="mt-3 text-xs text-slate-400">
        {lastPoll ? `Last checked ${lastPoll.toLocaleTimeString()}` : ''}
      </p>

      <span className="mt-2 inline-block rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        Phase 11 — Observer
      </span>
    </article>
  )
}
