/** Vertical event timeline with neon connector line. */
export default function Timeline({ items }) {
  if (!items || items.length === 0) {
    return (
      <div className="text-sentinel-muted text-xs tracking-widest py-6 text-center">
        NO DATED EVENTS EXTRACTED
      </div>
    )
  }

  const sorted = [...items].sort((a, b) => (a.date > b.date ? 1 : -1))

  return (
    <div className="relative pl-6">
      <div className="absolute left-1.5 top-1 bottom-1 w-px bg-sentinel-neon/40" />
      {sorted.map((it, i) => (
        <div key={i} className="relative mb-6 last:mb-0">
          <span className="absolute -left-6 top-1 h-3 w-3 rounded-full border-2 border-sentinel-neon bg-sentinel-bg shadow-neon" />
          <div className="text-[10px] tracking-[0.3em] text-sentinel-cyan">
            {it.date}
          </div>
          <div className="text-sm text-sentinel-text mt-0.5">
            {it.title}
          </div>
          <div className="text-[10px] tracking-widest text-sentinel-muted uppercase mt-0.5">
            {it.event_type}
          </div>
          {it.detail && (
            <p className="text-[11px] text-sentinel-muted mt-1 leading-relaxed">
              {it.detail}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
