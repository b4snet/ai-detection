import { useState } from 'react'

const TYPE_COLORS = {
  person: 'text-sentinel-neon border-sentinel-neon/50',
  organization: 'text-sentinel-amber border-sentinel-amber/50',
  location: 'text-sentinel-cyan border-sentinel-cyan/50',
  vehicle: 'text-purple-300 border-purple-400/50',
  object: 'text-pink-300 border-pink-400/50',
}

/** Expandable entity profile card. */
export default function EntityCard({ entity }) {
  const [open, setOpen] = useState(false)
  const type = entity.entity_type || 'entity'
  const tone = TYPE_COLORS[type] || TYPE_COLORS.object
  const pct = Math.round((entity.confidence || 0) * 100)

  return (
    <div className="border border-sentinel-border bg-sentinel-panel2/60">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-sentinel-neon/5 transition-colors"
      >
        <div className="min-w-0">
          <div className="text-sm text-sentinel-text truncate">{entity.name}</div>
          <div className={`inline-block mt-1 text-[9px] px-1.5 py-0.5 border tracking-widest uppercase ${tone}`}>
            {type}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-lg font-bold text-sentinel-neon">{pct}%</div>
          <div className="text-[9px] text-sentinel-muted tracking-widest">
            {entity.public_mentions || 0} MENTIONS
          </div>
        </div>
      </button>

      {open && (
        <div className="border-t border-sentinel-border px-4 py-3 space-y-3 text-[11px]">
          {entity.description && (
            <p className="text-sentinel-muted leading-relaxed">{entity.description}</p>
          )}

          {entity.aliases?.length > 0 && (
            <div>
              <div className="panel-title mb-1">ALIASES</div>
              <div className="flex flex-wrap gap-1.5">
                {entity.aliases.map((a) => (
                  <span key={a} className="border border-sentinel-border px-2 py-0.5 text-sentinel-cyan">
                    {a}
                  </span>
                ))}
              </div>
            </div>
          )}

          {entity.risk_indicators?.length > 0 && (
            <div>
              <div className="panel-title mb-1">RISK INDICATORS</div>
              <ul className="space-y-1">
                {entity.risk_indicators.map((r, i) => (
                  <li key={i} className="text-sentinel-amber">
                    ▸ {r.indicator}
                    {r.note && <span className="text-sentinel-muted"> — {r.note}</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {entity.associated_sources?.length > 0 && (
            <div>
              <div className="panel-title mb-1">ASSOCIATED SOURCES ({entity.associated_sources.length})</div>
              <ul className="space-y-1">
                {entity.associated_sources.slice(0, 5).map((s, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-sentinel-neon">▪</span>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sentinel-cyan underline decoration-dotted hover:text-sentinel-neon break-all"
                    >
                      {s.title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="text-sentinel-muted tracking-widest">
            VERIFICATION: <span className="text-sentinel-amber">{entity.verification || 'PENDING HUMAN REVIEW'}</span>
          </div>
        </div>
      )}
    </div>
  )
}
