import { useSentinel } from '../context/SentinelContext.jsx'

function Field({ label, value, tone = 'text-sentinel-neon' }) {
  return (
    <div className="py-2 border-b border-sentinel-border/60 last:border-b-0">
      <div className="text-[9px] tracking-[0.3em] text-sentinel-muted mb-0.5">
        {label}
      </div>
      <div className={`text-xs tracking-wider ${tone}`}>{value}</div>
    </div>
  )
}

export default function StatusStrip() {
  const { status } = useSentinel()
  const s = status || {}

  return (
    <div className="panel corner-frame p-5 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-x-6">
      <Field label="SYSTEM STATUS" value={s.status || '...'}
        tone={s.status === 'ONLINE' ? 'text-sentinel-neon glow-text' : 'text-sentinel-red'} />
      <Field label="AI ENGINE" value={s.ai_engine || '...'}
        tone={s.ollama_online ? 'text-sentinel-neon' : 'text-sentinel-amber'} />
      <Field label="AI MODE" value={(s.ai_mode || 'auto').toUpperCase()} />
      <Field label="DATA CONNECTION" value={s.data_connection || '...'} />
      <Field label="LAST UPDATE" value={(s.last_update || '--').slice(11, 19) + ' UTC'} />
      <Field label="VISION STACK" value={(s.vision_stack || '--').toUpperCase()} tone="text-sentinel-cyan" />
    </div>
  )
}
