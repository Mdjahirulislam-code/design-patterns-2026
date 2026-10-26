import { useCallback, useEffect, useState } from 'react'
import {
  fetchReadings,
  readSensorNow,
  updateSampling,
  type ReadingDto,
  type ReadingSource,
  type SensorDto,
} from '../../services/api'

// TEMPORARY (Phase 5): the card polls the latest stored reading so rows written
// by the simulation sampler show up without pressing "Read now".
// Phase 12 replaces this poll with the dashboard WebSocket (reading.created).
const POLL_INTERVAL_MS = 3000

const MIN_INTERVAL_SECONDS = 5

const SOURCE_BADGE: Record<ReadingSource, string> = {
  simulation: 'bg-sky-50 text-sky-700 ring-sky-200',
  mqtt: 'bg-violet-50 text-violet-700 ring-violet-200',
  vendor: 'bg-amber-50 text-amber-700 ring-amber-200',
}

function readableType(deviceType: string) {
  return deviceType.replaceAll('_', ' ')
}

function formatValue(reading: ReadingDto) {
  const digits = reading.unit === 'lux' ? 0 : 2
  return `${reading.value.toFixed(digits)} ${reading.unit}`
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString()
}

function errorText(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback
}

type Props = {
  sensor: SensorDto
}

export default function SensorCard({ sensor }: Props) {
  const protocol = String(sensor.default_config.protocol ?? 'simulation')
  const isVendor = sensor.default_config.vendor_stub === true
  const isMqtt = protocol === 'mqtt'

  // latest reading, always loaded from the database
  const [reading, setReading] = useState<ReadingDto | null>(null)
  const [loadingReading, setLoadingReading] = useState(true)
  const [readingError, setReadingError] = useState<string | null>(null)
  const [readingNow, setReadingNow] = useState(false)

  // sampling settings saved in the devices table
  const [savedInterval, setSavedInterval] = useState(sensor.sampling_interval_seconds)
  const [savedTracking, setSavedTracking] = useState(sensor.tracking_enabled)
  const [intervalInput, setIntervalInput] = useState(String(sensor.sampling_interval_seconds))
  const [saving, setSaving] = useState(false)
  const [samplingError, setSamplingError] = useState<string | null>(null)
  const [samplingSaved, setSamplingSaved] = useState(false)

  const loadLatest = useCallback(async () => {
    const rows = await fetchReadings(sensor.id, 1)
    return rows[0] ?? null
  }, [sensor.id])

  useEffect(() => {
    let cancelled = false

    const tick = async () => {
      try {
        const latest = await loadLatest()
        if (cancelled) return
        setReading(latest)
        setReadingError(null)
      } catch (err) {
        if (!cancelled) setReadingError(errorText(err, 'Could not load the latest reading'))
      } finally {
        if (!cancelled) setLoadingReading(false)
      }
    }

    void tick()
    // Temporary poll, see POLL_INTERVAL_MS above. Removed in Phase 12.
    const timer = window.setInterval(() => void tick(), POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [loadLatest])

  const readNow = async () => {
    try {
      setReadingNow(true)
      setReadingError(null)
      setReading(await readSensorNow(sensor.id))
    } catch (err) {
      setReadingError(errorText(err, 'Could not read the sensor'))
    } finally {
      setReadingNow(false)
    }
  }

  const saveSampling = async (intervalSeconds: number, tracking: boolean) => {
    try {
      setSaving(true)
      setSamplingError(null)
      setSamplingSaved(false)
      const saved = await updateSampling(sensor.id, {
        sampling_interval_seconds: intervalSeconds,
        tracking_enabled: tracking,
      })
      setSavedInterval(saved.sampling_interval_seconds)
      setSavedTracking(saved.tracking_enabled)
      setIntervalInput(String(saved.sampling_interval_seconds))
      setSamplingSaved(true)
    } catch (err) {
      setSamplingError(errorText(err, 'Could not save sampling settings'))
    } finally {
      setSaving(false)
    }
  }

  const parsedInterval = Number(intervalInput)
  const intervalValid = Number.isInteger(parsedInterval) && parsedInterval >= MIN_INTERVAL_SECONDS
  const intervalChanged = intervalValid && parsedInterval !== savedInterval

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="font-medium text-slate-900">{sensor.display_name}</h4>
          <p className="mt-1 text-sm capitalize text-slate-500">
            {readableType(sensor.device_type)} · {sensor.device_family}
          </p>
        </div>
        <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
          {isVendor ? 'vendor stub' : protocol}
        </span>
      </div>

      {/* Latest stored reading */}
      <div className="mt-4 rounded-md border border-slate-200 bg-white p-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Latest reading</p>
            {loadingReading ? (
              <p className="mt-1 text-sm text-slate-500">Loading…</p>
            ) : reading ? (
              <>
                <p className="mt-1 text-2xl font-semibold text-slate-900">{formatValue(reading)}</p>
                <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span
                    className={`rounded-full px-2 py-0.5 font-medium ring-1 ${SOURCE_BADGE[reading.source] ?? 'bg-slate-100 text-slate-600 ring-slate-200'}`}
                  >
                    {reading.source}
                  </span>
                  <span>at {formatTime(reading.recorded_at)}</span>
                </p>
              </>
            ) : (
              <p className="mt-1 text-sm text-slate-500">No readings stored yet.</p>
            )}
          </div>

          <button
            type="button"
            onClick={() => void readNow()}
            disabled={readingNow || isMqtt}
            title={isMqtt ? 'MQTT devices send their own readings (Phase 12)' : undefined}
            className="shrink-0 rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {readingNow ? 'Reading…' : 'Read now'}
          </button>
        </div>

        {isMqtt && (
          <p className="mt-2 text-xs text-slate-500">
            MQTT sensors push their own readings. Delivery arrives in Phase 12.
          </p>
        )}

        {readingError && (
          <p className="mt-2 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700 ring-1 ring-red-200">
            {readingError}
          </p>
        )}
      </div>

      {/* Sampling settings */}
      <div className="mt-3 rounded-md border border-slate-200 bg-white p-3">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm text-slate-600">
            <span className="block text-xs uppercase tracking-wide text-slate-500">
              Interval (seconds)
            </span>
            <input
              type="number"
              min={MIN_INTERVAL_SECONDS}
              step={1}
              value={intervalInput}
              onChange={(event) => {
                setIntervalInput(event.target.value)
                setSamplingSaved(false)
              }}
              disabled={saving}
              className="mt-1 w-28 rounded-md border border-slate-300 px-2 py-1.5 text-sm text-slate-900 disabled:opacity-50"
            />
          </label>

          <button
            type="button"
            onClick={() => void saveSampling(parsedInterval, savedTracking)}
            disabled={saving || !intervalChanged}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>

          <label className="ml-auto flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={savedTracking}
              onChange={(event) => void saveSampling(savedInterval, event.target.checked)}
              disabled={saving}
              className="h-4 w-4 rounded border-slate-300 accent-emerald-600"
            />
            Tracking {savedTracking ? 'on' : 'off'}
          </label>
        </div>

        {!intervalValid && (
          <p className="mt-2 text-xs text-red-700">
            Interval must be a whole number of at least {MIN_INTERVAL_SECONDS} seconds.
          </p>
        )}

        {samplingError && (
          <p className="mt-2 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700 ring-1 ring-red-200">
            {samplingError}
          </p>
        )}

        {samplingSaved && !samplingError && (
          <p className="mt-2 text-xs text-emerald-700">Sampling settings saved.</p>
        )}

        <p className="mt-2 text-xs text-slate-500">
          {isMqtt
            ? 'The sampler skips MQTT devices. The device itself follows this interval.'
            : isVendor
              ? 'The vendor stub is read with “Read now” only. The sampler skips it.'
              : savedTracking
                ? `The simulation sampler stores a reading every ${savedInterval} s.`
                : 'Tracking is off: the sampler does not record this sensor.'}
        </p>
      </div>
    </div>
  )
}
