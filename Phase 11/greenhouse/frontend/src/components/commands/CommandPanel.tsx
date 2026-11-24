import { useCallback, useEffect, useState } from 'react'
import {
  fetchCommands,
  fetchDevices,
  postCommand,
  type CommandLogDto,
  type CommandStatus,
  type CommandType,
  type DeviceDto,
} from '../../services/api'
import ActuatorStateBadge from '../devices/ActuatorStateBadge'

const HISTORY_LIMIT = 50

const STATUS_BADGE: Record<CommandStatus, string> = {
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  failed: 'bg-red-50 text-red-700 ring-red-200',
  rejected: 'bg-amber-50 text-amber-700 ring-amber-200',
}

const BUTTONS: { type: CommandType; label: string }[] = [
  { type: 'start_pump', label: 'Start pump' },
  { type: 'stop_pump', label: 'Stop pump' },
  { type: 'set_light_level', label: 'Set light level' },
]

function errorText(err: unknown, fallback: string) {
  return err instanceof Error ? err.message : fallback
}

/**
 * Phase 10 — Command: actuator controls and the command history.
 * A button is disabled when its command is not in the actuator's
 * allowed_commands. The backend still checks every command itself.
 */
export default function CommandPanel() {
  const [actuators, setActuators] = useState<DeviceDto[]>([])
  const [history, setHistory] = useState<CommandLogDto[]>([])
  const [levels, setLevels] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CommandLogDto | null>(null)

  // Actuators (state + allowed_commands) and history both come from the database.
  const load = useCallback(async () => {
    try {
      const [devices, commands] = await Promise.all([
        fetchDevices({ role: 'actuator' }),
        fetchCommands(HISTORY_LIMIT),
      ])
      setActuators(devices)
      setHistory(commands)
    } catch (err) {
      setError(errorText(err, 'Could not load the controls'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const send = async (device: DeviceDto, type: CommandType) => {
    const payload: Record<string, unknown> = {}
    if (type === 'set_light_level') {
      const level = Number(levels[device.id] ?? '1')
      payload.level = Number.isFinite(level) ? level : 1
    }

    try {
      setBusy(`${device.id}:${type}`)
      setError(null)
      setResult(null)
      setResult(await postCommand(type, device.id, payload))
    } catch (err) {
      setError(errorText(err, 'Could not send the command'))
    } finally {
      setBusy(null)
      await load() // reload actuators and history after every click
    }
  }

  const nameOf = (id: string) =>
    actuators.find((device) => device.id === id)?.display_name ?? `${id.slice(0, 8)}…`

  return (
    <article id="controls" className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">Controls</h3>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Send commands to the actuators. A button is disabled when the actuator's current
            state does not allow that command. Every command is stored in the history below as
            success, failed or rejected.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading || busy !== null}
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

      {result && (
        <div
          className={`mt-4 rounded-md px-3 py-2 text-sm ring-1 ${STATUS_BADGE[result.status] ?? STATUS_BADGE.failed}`}
        >
          {result.command_type}: {result.status}
          {result.error_message ? `. ${result.error_message}` : ''}
        </div>
      )}

      {loading ? (
        <p className="mt-5 text-sm text-slate-500">Loading…</p>
      ) : actuators.length === 0 ? (
        <p className="mt-5 rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          No actuators yet. Provision a device family in the Devices section first.
        </p>
      ) : (
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {actuators.map((device) => {
            const allowed = device.allowed_commands ?? []
            return (
              <div key={device.id} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h4 className="font-medium text-slate-900">{device.display_name}</h4>
                    <p className="text-xs text-slate-500">{device.device_type.replaceAll('_', ' ')}</p>
                  </div>
                  {device.state && (
                    <ActuatorStateBadge state={device.state} allowedCommands={allowed} />
                  )}
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {BUTTONS.map((button) => {
                    const isAllowed = allowed.includes(button.type)
                    return (
                      <button
                        key={button.type}
                        type="button"
                        onClick={() => void send(device, button.type)}
                        disabled={!isAllowed || busy !== null}
                        title={
                          isAllowed
                            ? undefined
                            : `Not allowed while the actuator is ${device.state ?? 'in this state'}`
                        }
                        className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {busy === `${device.id}:${button.type}` ? 'Sending…' : button.label}
                      </button>
                    )
                  })}

                  <label className="flex items-center gap-1 text-xs text-slate-500">
                    level
                    <input
                      type="number"
                      min={0}
                      step={0.1}
                      value={levels[device.id] ?? '1'}
                      onChange={(event) =>
                        setLevels((current) => ({ ...current, [device.id]: event.target.value }))
                      }
                      className="w-16 rounded-md border border-slate-300 px-2 py-1 text-sm text-slate-900"
                    />
                  </label>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <h4 className="mt-6 text-sm font-semibold text-slate-700">Command history</h4>

      {!loading && history.length === 0 ? (
        <p className="mt-2 rounded-md border border-dashed border-slate-300 p-4 text-sm text-slate-500">
          No commands yet. Press a button above to send the first one.
        </p>
      ) : (
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4 font-medium">Time</th>
                <th className="py-2 pr-4 font-medium">Device</th>
                <th className="py-2 pr-4 font-medium">Command</th>
                <th className="py-2 pr-4 font-medium">Payload</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                <th className="py-2 font-medium">Message</th>
              </tr>
            </thead>
            <tbody>
              {history.map((row) => (
                <tr key={row.id} className="border-b border-slate-100 align-top">
                  <td className="whitespace-nowrap py-2 pr-4 text-slate-600">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                  <td className="py-2 pr-4 font-medium text-slate-800">{nameOf(row.device_id)}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-slate-700">{row.command_type}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-slate-500">
                    {Object.keys(row.payload).length > 0 ? JSON.stringify(row.payload) : '—'}
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${STATUS_BADGE[row.status] ?? STATUS_BADGE.failed}`}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td className="py-2 text-slate-700">{row.error_message ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <span className="mt-4 inline-block rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
        Phase 10 — Command
      </span>
    </article>
  )
}
