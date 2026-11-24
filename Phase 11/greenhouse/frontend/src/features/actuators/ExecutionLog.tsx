import { useCallback, useEffect, useState } from 'react'
import {
  applyActuatorCommand,
  fetchDevices,
  fetchExecutions,
  type DeviceDto,
  type ExecutionDto,
} from '../../services/api'

const LIMIT = 20

function errorText(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString()
}

function ResultBadge({ success }: { success: boolean }) {
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${
        success
          ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
          : 'bg-red-50 text-red-700 ring-red-200'
      }`}
    >
      {success ? 'success' : 'failed'}
    </span>
  )
}

/**
 * Phase 9 — Decorator: the rows of actuator_execution_log, plus a small demo
 * control that sends a command through the decorated actuator port.
 * No policy is checked here. The backend decorators decide and log.
 */
export default function ExecutionLog() {
  const [executions, setExecutions] = useState<ExecutionDto[]>([])
  const [actuators, setActuators] = useState<DeviceDto[]>([])
  const [deviceId, setDeviceId] = useState('')
  const [command, setCommand] = useState('start')

  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [applyError, setApplyError] = useState<string | null>(null)
  const [applyNote, setApplyNote] = useState<string | null>(null)

  // The table always comes from the database, also after a blocked attempt.
  const load = useCallback(async () => {
    try {
      setError(null)
      const [rows, devices] = await Promise.all([
        fetchExecutions(LIMIT),
        fetchDevices({ role: 'actuator' }),
      ])
      setExecutions(rows)
      setActuators(devices)
      setDeviceId((current) => current || (devices[0]?.id ?? ''))
    } catch (err) {
      setError(errorText(err, 'Could not load the execution log'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const apply = async () => {
    if (!deviceId) return
    try {
      setApplying(true)
      setApplyError(null)
      setApplyNote(null)
      await applyActuatorCommand(deviceId, command)
      setApplyNote(`Command “${command}” was applied.`)
    } catch (err) {
      // a blocked attempt (409) lands here; its row is already in the log
      setApplyError(errorText(err, 'Could not apply the command'))
    } finally {
      setApplying(false)
      await load()
    }
  }

  const nameOf = (id: string) =>
    actuators.find((device) => device.id === id)?.display_name ?? `${id.slice(0, 8)}…`

  return (
    <article id="executions" className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Actuator execution log</h3>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Every attempt to send a command to an actuator is stored here. The command is not
            validated in this phase, so any command succeeds until the actuator has been{' '}
            <code>running</code> for 30 minutes. A successful row has an empty message and the
            policy <code>logging</code>. A blocked row shows <code>Max run time exceeded</code>{' '}
            with the policies <code>maxRunTime</code> and <code>logging</code>.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void load()}
          disabled={loading || applying}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      {/* Demo apply (Phase 10 replaces this with commands) */}
      <div className="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4">
        {actuators.length === 0 ? (
          <p className="text-sm text-slate-500">
            {loading
              ? 'Loading…'
              : 'No actuators yet. Provision a device family in the Devices section first.'}
          </p>
        ) : (
          <div className="flex flex-wrap items-end gap-3">
            <label className="text-sm text-slate-600">
              <span className="block text-xs uppercase tracking-wide text-slate-500">Actuator</span>
              <select
                value={deviceId}
                onChange={(event) => setDeviceId(event.target.value)}
                disabled={applying}
                className="mt-1 rounded-md border border-slate-300 bg-white px-2 py-2 text-sm text-slate-900 disabled:opacity-50"
              >
                {actuators.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.display_name} ({device.state ?? 'idle'})
                  </option>
                ))}
              </select>
            </label>

            <label className="text-sm text-slate-600">
              <span className="block text-xs uppercase tracking-wide text-slate-500">Command</span>
              <input
                type="text"
                value={command}
                onChange={(event) => setCommand(event.target.value)}
                disabled={applying}
                className="mt-1 w-40 rounded-md border border-slate-300 px-2 py-2 text-sm text-slate-900 disabled:opacity-50"
              />
            </label>

            <button
              type="button"
              onClick={() => void apply()}
              disabled={applying || !deviceId}
              className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {applying ? 'Applying…' : 'Apply command'}
            </button>
          </div>
        )}

        {applyError && (
          <p className="mt-3 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700 ring-1 ring-red-200">
            {applyError}
          </p>
        )}

        {applyNote && !applyError && <p className="mt-3 text-xs text-emerald-700">{applyNote}</p>}
      </div>

      {/* Rows from actuator_execution_log */}
      {loading ? (
        <p className="mt-5 text-sm text-slate-500">Loading executions…</p>
      ) : executions.length === 0 ? (
        <p className="mt-5 rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          No executions yet. Apply a command to an actuator to create the first row.
        </p>
      ) : (
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4 font-medium">Time</th>
                <th className="py-2 pr-4 font-medium">Device</th>
                <th className="py-2 pr-4 font-medium">Result</th>
                <th className="py-2 pr-4 font-medium">Policies</th>
                <th className="py-2 font-medium">Message</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 align-top">
                  <td className="whitespace-nowrap py-2 pr-4 text-slate-600">
                    {formatTime(row.created_at)}
                  </td>
                  <td className="py-2 pr-4 font-medium text-slate-800">{nameOf(row.device_id)}</td>
                  <td className="py-2 pr-4">
                    <ResultBadge success={row.success} />
                  </td>
                  <td className="py-2 pr-4">
                    <span className="flex flex-wrap gap-1">
                      {row.policy_applied.map((policy) => (
                        <span
                          key={policy}
                          className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-slate-700"
                        >
                          {policy}
                        </span>
                      ))}
                    </span>
                  </td>
                  <td className="py-2 text-slate-700">{row.message ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-slate-500">Showing the newest {LIMIT} rows.</p>
        </div>
      )}

      <span className="mt-4 inline-block rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        Phase 9 — Decorator
      </span>
    </article>
  )
}
