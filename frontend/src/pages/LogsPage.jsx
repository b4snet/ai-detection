import { useSentinel } from '../context/SentinelContext.jsx'
import Panel from '../components/Panel.jsx'
import SystemLog from '../components/SystemLog.jsx'

export default function LogsPage() {
  const { status } = useSentinel()

  const stats = [
    { label: 'ANALYSES', value: status?.analyses_count ?? '--' },
    { label: 'ENTITIES', value: status?.entities_count ?? '--' },
    { label: 'UPTIME', value: `${Math.floor((status?.uptime_seconds || 0) / 60)}m ${(status?.uptime_seconds || 0) % 60}s` },
    { label: 'AI MODE', value: (status?.ai_mode || '--').toUpperCase() },
  ]

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-[0.3em] text-sentinel-neon glow-text">
          SYSTEM LOG
        </h1>
        <p className="mt-2 text-[10px] tracking-[0.4em] text-sentinel-muted uppercase">
          Real-time operations feed
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((s) => (
          <div key={s.label} className="border border-sentinel-border bg-sentinel-panel2/60 p-4 text-center">
            <div className="text-2xl font-extrabold text-sentinel-neon glow-text">{s.value}</div>
            <div className="text-[9px] tracking-[0.3em] text-sentinel-muted mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      <Panel
        title="OPERATIONS ACTIVITY FEED"
        right={<span className="text-[9px] text-sentinel-cyan animate-pulseglow">● LIVE</span>}
      >
        <SystemLog height="h-[520px]" />
      </Panel>
    </div>
  )
}
