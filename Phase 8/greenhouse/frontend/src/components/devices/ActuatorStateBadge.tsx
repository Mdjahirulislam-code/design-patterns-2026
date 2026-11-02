import type { ActuatorStateName } from '../../services/api'

const COLORS: Record<ActuatorStateName, string> = {
  idle: 'bg-slate-100 text-slate-700 ring-slate-300',
  running: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  error: 'bg-red-50 text-red-700 ring-red-200',
  maintenance: 'bg-amber-50 text-amber-700 ring-amber-200',
  off: 'bg-zinc-200 text-zinc-600 ring-zinc-300',
}

function readable(text: string) {
  return text.replaceAll('_', ' ')
}

type Props = {
  state: ActuatorStateName
  allowedCommands: string[]
}

/** Phase 8: actuator state badge. The tooltip lists what the backend allows now. */
export default function ActuatorStateBadge({ state, allowedCommands }: Props) {
  const tooltip =
    allowedCommands.length > 0
      ? `Allowed now: ${allowedCommands.map(readable).join(', ')}`
      : 'No commands allowed in this state'

  return (
    <span
      title={tooltip}
      className={`cursor-help rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${
        COLORS[state] ?? COLORS.idle
      }`}
    >
      {state}
    </span>
  )
}
