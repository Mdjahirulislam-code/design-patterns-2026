import { useState } from 'react'
import {
  ACTUATOR_STATES,
  transitionActuator,
  type ActuatorStateDto,
  type ActuatorStateName,
} from '../../services/api'
import ActuatorStateBadge from './ActuatorStateBadge'

type Props = {
  deviceId: string
  state: ActuatorStateName
  allowedCommands: string[]
}

/**
 * Phase 8 demo control. The dropdown lists every other state; the backend
 * decides if the move is legal. An illegal move comes back as 409 and its
 * reason is shown under the control. Phase 10 replaces this with commands.
 */
export default function ActuatorStateControl({ deviceId, state, allowedCommands }: Props) {
  const [current, setCurrent] = useState<ActuatorStateDto>({
    device_id: deviceId,
    state,
    allowed_commands: allowedCommands,
    updated_at: null,
  })
  const [target, setTarget] = useState<ActuatorStateName | ''>('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const apply = async () => {
    if (!target) return
    try {
      setSaving(true)
      setError(null)
      setCurrent(await transitionActuator(deviceId, target))
      setTarget('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not change the state')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mt-4 border-t pt-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm text-slate-500">State</span>
        <ActuatorStateBadge state={current.state} allowedCommands={current.allowed_commands} />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <select
          value={target}
          onChange={(event) => {
            setTarget(event.target.value as ActuatorStateName | '')
            setError(null)
          }}
          disabled={saving}
          className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 disabled:opacity-50"
        >
          <option value="">Move to…</option>
          {ACTUATOR_STATES.filter((name) => name !== current.state).map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => void apply()}
          disabled={saving || !target}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? 'Saving…' : 'Apply'}
        </button>
      </div>

      {error && (
        <p className="mt-2 rounded-md bg-red-50 px-2 py-1 text-xs text-red-700 ring-1 ring-red-200">
          {error}
        </p>
      )}
    </div>
  )
}
