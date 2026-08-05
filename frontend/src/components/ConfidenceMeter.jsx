export default function ConfidenceMeter({ value, size = 'md' }) {
  const pct = Math.round((value || 0) * 100)
  const tone =
    pct >= 70 ? 'bg-sentinel-neon' : pct >= 40 ? 'bg-sentinel-amber' : 'bg-sentinel-cyan'
  const w = size === 'lg' ? 'h-3' : 'h-2'
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[9px] tracking-[0.25em] text-sentinel-muted">
          CONFIDENCE
        </span>
        <span className="text-xs text-sentinel-neon font-semibold">{pct}%</span>
      </div>
      <div className={`${w} w-full bg-sentinel-panel2 border border-sentinel-border overflow-hidden`}>
        <div
          className={`${tone} h-full transition-all duration-700`}
          style={{ width: `${pct}%`, boxShadow: '0 0 8px rgba(0,255,136,0.5)' }}
        />
      </div>
    </div>
  )
}
