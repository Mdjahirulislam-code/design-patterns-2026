/**
 * Dashboard placeholders. The element ids below are fixed by the course
 * requirements: later phases mount their features into these sections.
 */

type Placeholder = {
  id: string
  title: string
  description: string
  phase: string
}

const SECTIONS: Placeholder[] = [
  {
    id: 'sensors',
    title: 'Sensors',
    description: 'Temperature, humidity and soil moisture readings from greenhouse devices.',
    phase: 'Phase 2 — Factory Method',
  },
  {
    id: 'config',
    title: 'Configuration',
    description: 'Greenhouse-wide settings such as target ranges and units.',
    phase: 'Later phase',
  },
  {
    id: 'automation',
    title: 'Automation',
    description: 'Rules that react to readings, for example venting when it gets too warm.',
    phase: 'Later phase',
  },
  {
    id: 'overview',
    title: 'Overview',
    description: 'Aggregated state of the greenhouse at a glance.',
    phase: 'Later phase',
  },
  {
    id: 'controls',
    title: 'Controls',
    description: 'Manual commands for actuators: fans, vents, irrigation and lighting.',
    phase: 'Later phase',
  },
  {
    id: 'events',
    title: 'Events',
    description: 'Alarm and activity log produced by the system.',
    phase: 'Later phase',
  },
]

export default function DashboardPage() {
  return (
    <section>
      <h2 className="text-2xl font-bold text-slate-900">Dashboard</h2>
      <p className="mt-2 text-slate-600">
        Placeholder sections. Each one is filled in by a later phase of the course.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SECTIONS.map((section) => (
          <article
            key={section.id}
            id={section.id}
            className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
          >
            <h3 className="text-lg font-semibold text-slate-900">{section.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{section.description}</p>
            <span className="mt-4 inline-block rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500">
              {section.phase}
            </span>
          </article>
        ))}
      </div>
    </section>
  )
}
