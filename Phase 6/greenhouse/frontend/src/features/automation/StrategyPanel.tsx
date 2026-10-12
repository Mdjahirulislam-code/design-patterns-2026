import { useEffect, useState } from 'react'
import {
  evaluateLocation,
  fetchAutomationRule,
  fetchLocations,
  fetchStrategies,
  saveStrategy,
  type AutomationAction,
  type AutomationRuleDto,
  type LocationSummaryDto,
  type RecommendationDto,
  type StrategyOptionDto,
} from '../../services/api'

const ACTION_BADGE: Record<AutomationAction, string> = {
  irrigate: 'bg-sky-50 text-sky-700 ring-sky-200',
  wait: 'bg-slate-100 text-slate-700 ring-slate-200',
}

function errorText(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback
}

function ActionBadge({ action }: { action: AutomationAction }) {
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${ACTION_BADGE[action] ?? ACTION_BADGE.wait}`}
    >
      {action}
    </span>
  )
}

/** Phase 6 — Strategy: pick and save a strategy per location, then evaluate it. */
export default function StrategyPanel() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [strategies, setStrategies] = useState<StrategyOptionDto[]>([])
  const [locationId, setLocationId] = useState('')
  const [rule, setRule] = useState<AutomationRuleDto | null>(null)
  const [selectedKey, setSelectedKey] = useState('')
  const [result, setResult] = useState<RecommendationDto | null>(null)

  const [loading, setLoading] = useState(true)
  const [loadingRule, setLoadingRule] = useState(false)
  const [saving, setSaving] = useState(false)
  const [evaluating, setEvaluating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // locations + strategy list
  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const [locationList, strategyList] = await Promise.all([
          fetchLocations(),
          fetchStrategies(),
        ])
        if (cancelled) return
        setLocations(locationList)
        setStrategies(strategyList)
        if (locationList.length > 0) setLocationId(locationList[0].id)
      } catch (err) {
        if (!cancelled) setError(errorText(err, 'Could not load automation settings'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  // saved strategy of the chosen location
  useEffect(() => {
    if (!locationId) return
    let cancelled = false

    const load = async () => {
      try {
        setLoadingRule(true)
        setResult(null)
        setSuccess(null)
        setError(null)
        const saved = await fetchAutomationRule(locationId)
        if (cancelled) return
        setRule(saved)
        setSelectedKey(saved.strategy_key)
      } catch (err) {
        if (!cancelled) setError(errorText(err, 'Could not load the saved strategy'))
      } finally {
        if (!cancelled) setLoadingRule(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [locationId])

  const save = async () => {
    try {
      setSaving(true)
      setError(null)
      setSuccess(null)
      const saved = await saveStrategy(locationId, selectedKey)
      setRule(saved)
      setSuccess(`Strategy “${saved.strategy_key}” saved for this location.`)
    } catch (err) {
      setError(errorText(err, 'Could not save the strategy'))
    } finally {
      setSaving(false)
    }
  }

  const evaluate = async () => {
    try {
      setEvaluating(true)
      setError(null)
      setSuccess(null)
      setResult(await evaluateLocation(locationId))
    } catch (err) {
      setError(errorText(err, 'Could not evaluate the location'))
    } finally {
      setEvaluating(false)
    }
  }

  const unsaved = rule !== null && (selectedKey !== rule.strategy_key || rule.is_default)
  const selectedStrategy = strategies.find((s) => s.key === selectedKey)
  const busy = saving || evaluating || loadingRule

  return (
    <article
      id="automation"
      className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div>
        <h3 className="text-lg font-semibold text-slate-900">Automation strategy</h3>
        <p className="mt-2 text-sm text-slate-600">
          Choose how each location decides on irrigation. Evaluate uses the saved strategy, each
          zone's moisture thresholds and the latest stored reading of the moisture sensors in that
          zone.
        </p>
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      {success && (
        <div className="mt-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700 ring-1 ring-emerald-200">
          {success}
        </div>
      )}

      {loading ? (
        <p className="mt-5 text-sm text-slate-500">Loading…</p>
      ) : locations.length === 0 ? (
        <p className="mt-5 rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          No locations yet. Create one with <code>POST /api/locations/config</code> (see
          location.json), then assign a moisture sensor to one of its zones.
        </p>
      ) : (
        <>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <label className="text-sm text-slate-600">
              <span className="block text-xs uppercase tracking-wide text-slate-500">Location</span>
              <select
                value={locationId}
                onChange={(event) => setLocationId(event.target.value)}
                disabled={busy}
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-900 disabled:opacity-50"
              >
                {locations.map((location) => (
                  <option key={location.id} value={location.id}>
                    {location.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm text-slate-600">
              <span className="block text-xs uppercase tracking-wide text-slate-500">Strategy</span>
              <select
                value={selectedKey}
                onChange={(event) => {
                  setSelectedKey(event.target.value)
                  setSuccess(null)
                }}
                disabled={busy || !rule}
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-900 disabled:opacity-50"
              >
                {strategies.map((strategy) => (
                  <option key={strategy.key} value={strategy.key}>
                    {strategy.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {selectedStrategy && (
            <p className="mt-2 text-xs text-slate-500">{selectedStrategy.description}</p>
          )}

          {rule && (
            <p className="mt-1 text-xs text-slate-500">
              {rule.is_default
                ? `Nothing saved yet. Evaluate uses the default “${rule.strategy_key}”.`
                : `Saved strategy: “${rule.strategy_key}”.`}
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => void save()}
              disabled={busy || !unsaved || !selectedKey}
              className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Save strategy'}
            </button>

            <button
              type="button"
              onClick={() => void evaluate()}
              disabled={busy || !locationId}
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {evaluating ? 'Evaluating…' : 'Evaluate'}
            </button>

            {rule && selectedKey !== rule.strategy_key && (
              <span className="text-xs text-amber-700">
                Unsaved change. Evaluate still uses “{rule.strategy_key}”.
              </span>
            )}
          </div>

          {result && (
            <div className="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-wrap items-center gap-3">
                <ActionBadge action={result.action} />
                <span className="text-sm font-medium text-slate-900">{result.reason}</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Strategy “{result.strategy_key}” · evaluated at{' '}
                {new Date(result.evaluated_at).toLocaleTimeString()}
              </p>

              {result.zones.length > 0 && (
                <ul className="mt-4 space-y-2">
                  {result.zones.map((zone) => (
                    <li
                      key={zone.zone_id}
                      className="rounded-md border border-slate-200 bg-white p-3 text-sm"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium text-slate-900">{zone.zone_name}</span>
                        <ActionBadge action={zone.action} />
                      </div>
                      <p className="mt-1 text-slate-600">{zone.reason}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        Moisture {zone.moisture === null ? '—' : zone.moisture.toFixed(2)} · band{' '}
                        {zone.moisture_threshold_low.toFixed(2)}–
                        {zone.moisture_threshold_high.toFixed(2)}
                        {zone.light !== null && ` · light ${Math.round(zone.light)} lux`}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </>
      )}

      <span className="mt-4 inline-block rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        Phase 6 — Strategy
      </span>
    </article>
  )
}
