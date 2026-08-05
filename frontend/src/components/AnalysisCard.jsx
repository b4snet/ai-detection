import { NavLink } from 'react-router-dom'
import { api } from '../api/client'

function VerifiedBadge({ status }) {
  const text = status || 'PENDING HUMAN REVIEW'
  const tone =
    text.toUpperCase().includes('REVIEW') || text.toUpperCase().includes('PENDING')
      ? 'text-sentinel-amber border-sentinel-amber/50 bg-sentinel-amber/5'
      : 'text-sentinel-neon border-sentinel-neon/50 bg-sentinel-neon/5'
  return (
    <span className={`text-[9px] px-2 py-0.5 border tracking-widest ${tone}`}>
      {text}
    </span>
  )
}

export default function AnalysisCard({ a }) {
  const pct = Math.round((a.confidence || 0) * 100)
  return (
    <NavLink
      to={`/analysis/${a.id}`}
      className="panel p-4 hover:border-sentinel-neon hover:shadow-neon transition-all block"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[10px] text-sentinel-muted tracking-widest">
            ANALYSIS #{a.id} // {(a.created_at || '').slice(0, 19).replace('T', ' ')}
          </div>
          <div className="text-sm text-sentinel-text truncate mt-1">
            {a.filename || 'image'}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-2xl font-extrabold text-sentinel-neon glow-text">{pct}%</div>
          <VerifiedBadge status={a.verification} />
        </div>
      </div>
      {a.summary && (
        <p className="text-[11px] text-sentinel-muted mt-3 line-clamp-2 leading-relaxed">
          {a.summary}
        </p>
      )}
      <div className="mt-3 flex items-center justify-between">
        <span
          className={`text-[9px] tracking-widest ${
            a.status === 'complete'
              ? 'text-sentinel-neon'
              : a.status === 'error'
                ? 'text-sentinel-red'
                : 'text-sentinel-amber'
          }`}
        >
          {a.status.toUpperCase()}
        </span>
        <span className="text-[10px] text-sentinel-cyan tracking-widest">OPEN ▸</span>
      </div>
    </NavLink>
  )
}

export function ReportButtons({ id }) {
  return (
    <div className="flex gap-2 mt-2">
      <a
        href={api.reportPdf(id)}
        target="_blank"
        rel="noreferrer"
        className="btn-neon text-[10px]"
      >
        ⬇ PDF REPORT
      </a>
      <a
        href={api.reportJson(id)}
        target="_blank"
        rel="noreferrer"
        className="border border-sentinel-border text-sentinel-muted hover:border-sentinel-neon hover:text-sentinel-neon px-3 py-2 text-[10px] tracking-widest"
      >
        ⬇ JSON
      </a>
    </div>
  )
}
