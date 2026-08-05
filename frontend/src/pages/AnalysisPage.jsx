import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api/client'
import Panel from '../components/Panel.jsx'
import ConfidenceMeter from '../components/ConfidenceMeter.jsx'
import KnowledgeGraph from '../components/KnowledgeGraph.jsx'
import Timeline from '../components/Timeline.jsx'
import EntityCard from '../components/EntityCard.jsx'
import { ReportButtons } from '../components/AnalysisCard.jsx'

function Row({ label, value, ok }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-sentinel-border/50 last:border-b-0">
      <span className="text-[10px] tracking-[0.25em] text-sentinel-muted">{label}</span>
      <span className={`text-xs tracking-widest ${ok ? 'text-sentinel-neon glow-text' : 'text-sentinel-red'}`}>
        {value}
      </span>
    </div>
  )
}

export default function AnalysisPage() {
  const { id } = useParams()
  const [a, setA] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let live = true
    const load = async () => {
      try {
        const data = await api.analysis(id)
        if (live) setA(data)
      } catch (e) {
        if (live) setError(String(e.message || e))
      }
    }
    load()
    const t = setInterval(load, 3000)
    return () => { live = false; clearInterval(t) }
  }, [id])

  if (error && !a) {
    return (
      <div className="max-w-2xl mx-auto text-center pt-20">
        <div className="text-sentinel-red text-xs tracking-widest mb-4">⚠ {error}</div>
        <Link to="/scan" className="btn-neon">BACK TO UPLOAD</Link>
      </div>
    )
  }
  if (!a) {
    return (
      <div className="text-center pt-24 text-sentinel-muted text-xs tracking-[0.3em] animate-blink">
        RETRIEVING INTELLIGENCE PACKET...
      </div>
    )
  }

  const v = a.vision || {}
  const faces = v.faces || {}
  const text = v.text || {}
  const loc = v.location || {}
  const objects = v.objects || []
  const vehicles = v.vehicles || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="text-[10px] tracking-[0.3em] text-sentinel-muted">
            INTELLIGENCE PRODUCT // ANALYSIS #{a.id}
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold tracking-widest text-sentinel-neon glow-text mt-1">
            {a.filename}
          </h1>
          <div className="mt-1 text-[10px] tracking-widest text-sentinel-muted">
            CAPTURED {a.timestamp ? a.timestamp.slice(0, 19).replace('T', ' ') : ''} UTC
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[9px] tracking-[0.3em] text-sentinel-muted">OVERALL CONFIDENCE</div>
            <div className="text-4xl font-extrabold text-sentinel-neon glow-text">
              {Math.round((a.confidence || 0) * 100)}%
            </div>
          </div>
          <ReportButtons id={a.id} />
        </div>
      </div>

      {/* Meta strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetaBox label="VERIFICATION" value={a.verification || 'PENDING HUMAN REVIEW'} tone="text-sentinel-amber" />
        <MetaBox label="STATUS" value={a.status} tone="text-sentinel-neon" />
        <MetaBox label="RESOLUTION" value={`${v.width || '-'} × ${v.height || '-'} px`} tone="text-sentinel-cyan" />
        <MetaBox label="FORMAT" value={(v.format || '--').toUpperCase()} tone="text-sentinel-text" />
      </div>

      {/* Image + visual intel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel title="EVIDENCE IMAGE">
          <div className="relative border border-sentinel-border bg-black/60 overflow-hidden">
            <img
              src={a.image_url || `/uploads/${a.filename}`}
              alt={a.filename}
              className="w-full max-h-[420px] object-contain"
            />
            <div className="absolute inset-0 pointer-events-none animate-scan bg-gradient-to-b from-transparent via-sentinel-neon/10 to-transparent" />
            <div className="absolute top-2 left-2 bg-black/70 border border-sentinel-neon/40 px-2 py-0.5 text-[9px] tracking-widest text-sentinel-neon">
              EVIDENCE://{a.id}
            </div>
            {v.gps && Object.keys(v.gps).length > 0 && (
              <div className="absolute bottom-2 left-2 bg-black/70 border border-sentinel-cyan/40 px-2 py-0.5 text-[9px] tracking-widest text-sentinel-cyan">
                GPS {v.gps.lat}, {v.gps.lon}
              </div>
            )}
          </div>
        </Panel>

        <div className="space-y-6">
          <Panel title="VISUAL INTELLIGENCE">
            <Row label="FACE PRESENCE" value={faces.detected ? 'YES' : 'NO'} ok={faces.detected} />
            <Row label="PERSONS IN FRAME" value={v.persons || 0} ok={(v.persons || 0) > 0} />
            <Row label="VEHICLE DETECTED" value={vehicles.length ? 'YES' : 'NO'} ok={vehicles.length > 0} />
            <Row label="TEXT FOUND" value={text.found ? 'YES' : 'NO'} ok={text.found} />
            <Row label="LOCATION CLUES" value={loc.found ? 'FOUND' : 'NONE'} ok={loc.found} />
            <Row label="LICENSE PLATES" value={v.plates?.length ? v.plates.join(', ') : 'NONE'} ok={v.plates?.length > 0} />
            {v.taken_at && <Row label="DATE TAKEN" value={v.taken_at} ok />}
            {v.camera_model && <Row label="CAMERA" value={v.camera_model} ok />}
          </Panel>

          {(v.colors?.length > 0) && (
            <Panel title="COLOR PROFILE">
              <div className="flex flex-wrap gap-2">
                {v.colors.map((c) => (
                  <span key={c} className="border border-sentinel-border px-2 py-1 text-[10px] text-sentinel-cyan">
                    {c}
                  </span>
                ))}
              </div>
            </Panel>
          )}
        </div>
      </div>

      {/* Detections detail */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {(objects.length > 0 || vehicles.length > 0) && (
          <Panel title={`OBJECTS DETECTED (${objects.length})`}>
            <div className="space-y-1.5 max-h-64 overflow-y-auto pr-2">
              {[...objects, ...vehicles].map((o, i) => (
                <div key={i} className="flex items-center justify-between text-xs border-b border-sentinel-border/40 py-1">
                  <span className="text-sentinel-text tracking-wider">{o.label.toUpperCase()}</span>
                  <span className="text-sentinel-neon">{(o.confidence * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </Panel>
        )}

        {text.found && (
          <Panel title={`EXTRACTED TEXT (${text.fragments.length}) // OCR`}>
            <div className="space-y-1.5 max-h-64 overflow-y-auto pr-2">
              {text.fragments.map((f, i) => (
                <div key={i} className="border border-sentinel-border/40 px-3 py-1.5 text-xs text-sentinel-text/90">
                  <span className="text-sentinel-muted mr-2">[{String(i + 1).padStart(2, '0')}]</span>
                  {f}
                </div>
              ))}
            </div>
          </Panel>
        )}
      </div>

      {/* Location clues */}
      {loc.found && (
        <Panel title="LOCATION INTELLIGENCE">
          <div className="grid md:grid-cols-2 gap-4 text-xs">
            <div>
              <div className="panel-title mb-2">CLUES</div>
              <ul className="space-y-1">
                {loc.clues.map((c, i) => (
                  <li key={i} className="text-sentinel-text/90">▸ {c}</li>
                ))}
              </ul>
            </div>
            {loc.geohints.length > 0 && (
              <div>
                <div className="panel-title mb-2">GEOHINTS</div>
                {loc.geohints.map((g, i) => (
                  <div key={i} className="text-sentinel-cyan tracking-widest">▸ {g}</div>
                ))}
                <div className="mt-2 text-[9px] text-sentinel-muted">
                  Map pinning available in full report
                </div>
              </div>
            )}
          </div>
        </Panel>
      )}

      {/* AI Report Summary */}
      {(a.intelligence?.overview || a.intelligence?.key_observations?.length) && (
        <Panel title="AI INTELLIGENCE ASSESSMENT">
          <ConfidenceMeter value={a.confidence} size="lg" />
          <p className="mt-4 text-xs leading-relaxed text-sentinel-text/90">
            {a.intelligence.overview}
          </p>

          {(a.intelligence.key_observations || []).length > 0 && (
            <div className="mt-4">
              <div className="panel-title mb-2">KEY OBSERVATIONS</div>
              <ul className="space-y-1.5">
                {a.intelligence.key_observations.map((o, i) => (
                  <li key={i} className="text-[11px] text-sentinel-cyan">
                    ▸ {o}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 grid md:grid-cols-2 gap-4 text-[11px]">
            <div className="border border-sentinel-amber/40 bg-sentinel-amber/5 p-3">
              <div className="panel-title mb-1 text-sentinel-amber">RISK ASSESSMENT</div>
              <p className="text-sentinel-amber/90 leading-relaxed">
                {a.intelligence.risk_assessment}
              </p>
            </div>
            <div className="border border-sentinel-cyan/40 bg-sentinel-cyan/5 p-3">
              <div className="panel-title mb-1 text-sentinel-cyan">ANALYST RECOMMENDATION</div>
              <p className="text-sentinel-cyan/90 leading-relaxed">
                {a.intelligence.recommendation}
              </p>
            </div>
          </div>

          <div className="mt-4 text-[10px] tracking-widest text-sentinel-amber border border-sentinel-amber/30 px-3 py-2">
            ⚠ HUMAN ANALYST REVIEW REQUIRED BEFORE ANY OPERATIONAL USE
          </div>
        </Panel>
      )}

      {/* Entity profiles */}
      <div>
        <div className="panel-title mb-3">
          ENTITY INFORMATION PANEL ({a.entities?.length || 0})
        </div>
        {a.entities?.length === 0 ? (
          <div className="panel p-6 text-center text-sentinel-muted text-xs tracking-widest">
            NO ENTITIES EXTRACTED FROM EVIDENCE
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-3">
            {a.entities.map((e, i) => (
              <EntityCard key={i} entity={e} />
            ))}
          </div>
        )}
      </div>

      {/* Knowledge graph */}
      <Panel
        title="RELATIONSHIP INTELLIGENCE GRAPH"
        right={<span className="text-[9px] text-sentinel-muted">NETWORKX // FORCE-DIRECTED</span>}
      >
        <KnowledgeGraph graph={a.graph} height={480} />
      </Panel>

      {/* Timeline + Sources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel title="SOURCE TIMELINE">
          <Timeline items={a.timeline} />
        </Panel>

        <Panel title={`PUBLIC SOURCES (${a.sources?.length || 0})`}>
          {a.sources?.length === 0 ? (
            <div className="text-sentinel-muted text-xs tracking-widest text-center py-8">
              NO PUBLIC REFERENCES RETRIEVED
            </div>
          ) : (
            <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
              {a.sources.map((s, i) => (
                <div key={i} className="border border-sentinel-border p-3">
                  <div className="flex items-start justify-between gap-3">
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-sentinel-cyan underline decoration-dotted hover:text-sentinel-neon"
                    >
                      {s.title}
                    </a>
                    <span className="text-[9px] text-sentinel-muted shrink-0">
                      {Math.round((s.relevance || 0) * 100)}%
                    </span>
                  </div>
                  <div className="mt-1 text-[9px] tracking-widest text-sentinel-muted uppercase">
                    {s.source_type} // {s.published_at || 'n/d'} // {s.verified || 'UNVERIFIED'}
                  </div>
                  {s.snippet && (
                    <p className="mt-1.5 text-[10px] text-sentinel-muted/80 leading-relaxed">
                      {s.snippet}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>

      {/* Processing notes */}
      {v.notes?.length > 0 && (
        <Panel title="PIPELINE NOTES">
          <ul className="space-y-1">
            {v.notes.map((n, i) => (
              <li key={i} className="text-[11px] text-sentinel-muted">▸ {n}</li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  )
}

function MetaBox({ label, value, tone = 'text-sentinel-text' }) {
  return (
    <div className="border border-sentinel-border bg-sentinel-panel2/60 px-4 py-3">
      <div className="text-[9px] tracking-[0.25em] text-sentinel-muted">{label}</div>
      <div className={`text-xs mt-1 tracking-wider break-words ${tone}`}>{value}</div>
    </div>
  )
}
