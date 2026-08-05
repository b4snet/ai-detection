import { Link } from 'react-router-dom'
import { useSentinel } from '../context/SentinelContext.jsx'
import Panel from '../components/Panel.jsx'
import StatusStrip from '../components/StatusStrip.jsx'
import SystemLog from '../components/SystemLog.jsx'
import AnalysisCard from '../components/AnalysisCard.jsx'
import ConfidenceMeter from '../components/ConfidenceMeter.jsx'

function BigStat({ label, value, sub, tone = 'text-sentinel-neon' }) {
  return (
    <div className="border border-sentinel-border bg-sentinel-panel2/60 p-4 text-center">
      <div className={`text-3xl font-extrabold glow-text ${tone}`}>{value}</div>
      <div className="text-[9px] tracking-[0.3em] text-sentinel-muted mt-1">{label}</div>
      {sub && <div className="text-[9px] text-sentinel-cyan tracking-widest mt-1">{sub}</div>}
    </div>
  )
}

export default function Dashboard() {
  const { status, analyses, loading } = useSentinel()
  const s = status || {}
  const recent = (analyses || []).slice(0, 6)
  const avgConf =
    analyses?.length > 0
      ? analyses.reduce((a, x) => a + (x.confidence || 0), 0) / analyses.length
      : 0

  return (
    <div className="space-y-6">
      {/* Title block */}
      <div className="text-center py-4">
        <h1 className="text-3xl md:text-5xl font-extrabold tracking-[0.35em] text-sentinel-neon glow-text animate-flicker">
          SENTINEL AI
        </h1>
        <p className="mt-2 text-[11px] md:text-xs tracking-[0.5em] text-sentinel-muted uppercase">
          Intelligence Operations Center
        </p>
        <div className="mt-3 mx-auto h-px w-64 bg-gradient-to-r from-transparent via-sentinel-neon to-transparent" />
        <p className="mt-3 text-[10px] tracking-widest text-sentinel-muted max-w-xl mx-auto">
          RESPONSIBLE INTELLIGENCE ASSISTANCE — NO AUTONOMOUS CLASSIFICATION OF PERSONS
        </p>
      </div>

      <StatusStrip />

      {/* Offline / hosted preview notice */}
      {!loading && !status && (
        <div className="border border-sentinel-amber/50 bg-sentinel-amber/5 text-sentinel-amber p-3 text-center text-[10px] tracking-widest">
          UI PREVIEW — BACKEND OFFLINE. THIS HOSTED LINK SHOWS THE INTERFACE ONLY. RUN LOCALLY
          WITH <span className="font-bold">python run.py</span> AND OPEN http://localhost:5173 FOR THE FULL PIPELINE.
        </div>
      )}

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/scan" className="btn-neon text-center py-4 text-sm">
          ⇪ UPLOAD IMAGE FOR ANALYSIS
        </Link>
        <Link to="/search" className="border border-sentinel-border text-sentinel-cyan hover:border-sentinel-cyan hover:text-sentinel-cyan bg-sentinel-cyan/5 text-center py-4 text-sm tracking-widest">
          ⌕ SEARCH INTELLIGENCE
        </Link>
        <Link to="/logs" className="border border-sentinel-border text-sentinel-amber hover:border-sentinel-amber hover:text-sentinel-amber bg-sentinel-amber/5 text-center py-4 text-sm tracking-widest">
          ≣ VIEW SYSTEM LOG
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <BigStat label="ANALYSES RUN" value={s.analyses_count ?? '--'} />
        <BigStat label="ENTITIES INDEXED" value={s.entities_count ?? '--'} tone="text-sentinel-cyan" />
        <BigStat
          label="AI ENGINE"
          value={s.ollama_online ? 'LOCAL' : 'FALLBACK'}
          tone={s.ollama_online ? 'text-sentinel-neon' : 'text-sentinel-amber'}
        />
        <BigStat label="UPTIME" value={`${Math.floor((s.uptime_seconds || 0) / 60)}m`} tone="text-sentinel-red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Panel
            title="RECENT ANALYSES"
            right={<span className="text-[9px] text-sentinel-cyan">AUTO-REFRESH 5s</span>}
          >
            {loading ? (
              <div className="text-sentinel-muted text-xs animate-blink py-8 text-center">
                ESTABLISHING SECURE CHANNEL...
              </div>
            ) : recent.length === 0 ? (
              <div className="py-10 text-center">
                <div className="text-sentinel-muted text-xs tracking-widest mb-3">
                  NO INTELLIGENCE PRODUCTS YET
                </div>
                <Link to="/scan" className="btn-neon inline-block">
                  INITIATE FIRST ANALYSIS
                </Link>
              </div>
            ) : (
              <div className="grid sm:grid-cols-2 gap-3">
                {recent.map((a) => (
                  <AnalysisCard key={a.id} a={a} />
                ))}
              </div>
            )}
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="OPERATIONS OVERVIEW">
            <ConfidenceMeter value={avgConf} size="lg" />
            <div className="mt-4 space-y-2 text-[11px]">
              <div className="flex justify-between">
                <span className="text-sentinel-muted">VISION STACK</span>
                <span className="text-sentinel-cyan">{(s.vision_stack || '--').toUpperCase()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sentinel-muted">LLM MODEL</span>
                <span className="text-sentinel-neon">{s.model || '--'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sentinel-muted">AUTH MODE</span>
                <span className="text-sentinel-amber">AUTHORIZED ANALYST ONLY</span>
              </div>
            </div>
          </Panel>

          <Panel title="LIVE SYSTEM LOG">
            <SystemLog height="h-72" />
          </Panel>
        </div>
      </div>
    </div>
  )
}
