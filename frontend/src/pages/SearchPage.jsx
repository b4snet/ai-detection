import { useState } from 'react'
import { api } from '../api/client'
import Panel from '../components/Panel.jsx'
import Timeline from '../components/Timeline.jsx'
import EntityCard from '../components/EntityCard.jsx'

const MODES = ['OSINT', 'ENTITY INDEX']

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState('OSINT')
  const [loading, setLoading] = useState(false)
  const [osint, setOsint] = useState(null)
  const [entities, setEntities] = useState(null)
  const [error, setError] = useState('')

  const run = async (e) => {
    e?.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError('')
    try {
      if (mode === 'OSINT') {
        const r = await api.search(query, 12)
        setOsint(r)
        setEntities(null)
      } else {
        const r = await api.searchEntities(query)
        setEntities(r)
        setOsint(null)
      }
    } catch (err) {
      setError(String(err.message || err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-[0.3em] text-sentinel-neon glow-text">
          INTELLIGENCE SEARCH
        </h1>
        <p className="mt-2 text-[10px] tracking-[0.4em] text-sentinel-muted uppercase">
          Search entity // event // location
        </p>
      </div>

      <form onSubmit={run} className="panel p-4">
        <div className="flex gap-2 mb-3">
          {MODES.map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`px-4 py-1.5 text-[10px] tracking-widest border transition-colors
                ${mode === m
                  ? 'border-sentinel-neon text-sentinel-neon bg-sentinel-neon/10 shadow-neon'
                  : 'border-sentinel-border text-sentinel-muted hover:text-sentinel-neon'}`}
            >
              {m}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`SEARCH ${mode === 'OSINT' ? 'PUBLIC SOURCES' : 'LOCAL ENTITY INDEX'}...`}
            className="flex-1 bg-black/60 border border-sentinel-border px-4 py-3 text-sm text-sentinel-neon tracking-wider focus:border-sentinel-neon focus:shadow-neon outline-none placeholder:text-sentinel-muted"
          />
          <button type="submit" disabled={loading} className="btn-neon disabled:opacity-50">
            {loading ? 'QUERYING...' : '⌕ SEARCH'}
          </button>
        </div>
      </form>

      {error && (
        <div className="border border-sentinel-red text-sentinel-red text-xs px-4 py-3 tracking-widest">
          ⚠ {error}
        </div>
      )}

      {mode === 'OSINT' && osint && (
        <div className="grid lg:grid-cols-2 gap-6">
          <Panel title={`OSINT RESULTS (${osint.results?.length || 0})`}>
            {osint.results?.length === 0 ? (
              <div className="text-center text-sentinel-muted text-xs tracking-widest py-8">
                NO PUBLIC REFERENCES FOUND
              </div>
            ) : (
              <div className="space-y-3 max-h-[560px] overflow-y-auto pr-2">
                {osint.results.map((r, i) => (
                  <div key={i} className="border border-sentinel-border p-3">
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-sentinel-cyan underline decoration-dotted hover:text-sentinel-neon"
                    >
                      {r.title}
                    </a>
                    <div className="mt-1 text-[9px] tracking-widest text-sentinel-muted uppercase">
                      {r.source_type} // {r.source} // {r.published_at || 'n/d'} //
                      <span className="text-sentinel-amber"> {r.verified || 'UNVERIFIED'}</span>
                    </div>
                    {r.snippet && (
                      <p className="mt-1.5 text-[10px] text-sentinel-muted/80 leading-relaxed">
                        {r.snippet}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="DERIVED TIMELINE">
            <Timeline items={osint.timeline || []} />
          </Panel>
        </div>
      )}

      {mode === 'ENTITY INDEX' && entities && (
        <Panel title={`LOCAL ENTITY INDEX MATCHES (${entities.results?.length || 0})`}>
          {entities.results?.length === 0 ? (
            <div className="text-center text-sentinel-muted text-xs tracking-widest py-8">
              NO ENTITIES MATCH '{entities.query}'
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-3">
              {entities.results.map((e, i) => (
                <EntityCard key={i} entity={{ ...e, associated_sources: [], risk_indicators: [] }} />
              ))}
            </div>
          )}
        </Panel>
      )}
    </div>
  )
}
