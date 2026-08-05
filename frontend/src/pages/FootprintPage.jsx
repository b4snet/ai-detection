import { useState } from 'react'
import { api } from '../api/client'
import Panel from '../components/Panel.jsx'
import ConfidenceMeter from '../components/ConfidenceMeter.jsx'

const emptyForm = {
  name: '',
  email: '',
  username: '',
  domain: '',
  known_location: '',
  purpose: '',
  consent: false,
}

export default function FootprintPage() {
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  const run = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const r = await api.footprintAudit(form)
      setResult(r)
    } catch (err) {
      setError(String(err.message || err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-[0.25em] text-sentinel-neon glow-text">
          DIGITAL FOOTPRINT AUDIT
        </h1>
        <p className="mt-2 text-[10px] tracking-[0.35em] text-sentinel-muted uppercase">
          Consent-based public-source lead discovery // no face ID // no location tracking
        </p>
      </div>

      <Panel title="AUTHORIZED INPUT BOX">
        <form onSubmit={run} className="space-y-4">
          <div className="grid md:grid-cols-2 gap-3">
            <Input label="Known name" value={form.name} onChange={(v) => set('name', v)} placeholder="Jane Example" />
            <Input label="Email" value={form.email} onChange={(v) => set('email', v)} placeholder="jane@example.com" />
            <Input label="Username / handle" value={form.username} onChange={(v) => set('username', v)} placeholder="@example" />
            <Input label="Known website/domain" value={form.domain} onChange={(v) => set('domain', v)} placeholder="example.com" />
            <Input label="Known location context" value={form.known_location} onChange={(v) => set('known_location', v)} placeholder="Optional; user-provided only" />
            <Input label="Purpose / authorization" value={form.purpose} onChange={(v) => set('purpose', v)} placeholder="Self-audit / authorized investigation" />
          </div>

          <label className="flex gap-3 items-start border border-sentinel-amber/50 bg-sentinel-amber/5 p-3 text-xs text-sentinel-muted leading-relaxed">
            <input
              type="checkbox"
              checked={form.consent}
              onChange={(e) => set('consent', e.target.checked)}
              className="mt-1 accent-cyan-400"
            />
            <span>
              I confirm I have consent or lawful authorization. I will not use this for stalking,
              doxxing, harassment, phone scraping, face identification, or current/last-seen
              location tracking.
            </span>
          </label>

          <button disabled={loading} className="btn-neon disabled:opacity-50">
            {loading ? 'AUDITING PUBLIC SOURCES...' : '⌁ RUN FOOTPRINT AUDIT'}
          </button>
        </form>
      </Panel>

      {error && <div className="border border-sentinel-red text-sentinel-red text-xs px-4 py-3 tracking-widest">⚠ {error}</div>}

      {result && (
        <div className="grid lg:grid-cols-3 gap-6">
          <Panel title="AUDIT SUMMARY">
            <div className="space-y-4">
              <ConfidenceMeter value={result.confidence || 0} label="MATCH CONFIDENCE" />
              <div className="text-[10px] text-sentinel-muted leading-relaxed">{result.notice}</div>
              <div className="space-y-2">
                {(result.guardrails || []).map((g, i) => (
                  <div key={i} className="text-[10px] tracking-wider text-sentinel-amber">▸ {g}</div>
                ))}
              </div>
            </div>
          </Panel>

          <Panel title={`PUBLIC FINDINGS (${result.findings?.length || 0})`} className="lg:col-span-2">
            {!result.findings?.length ? (
              <div className="text-center text-sentinel-muted text-xs tracking-widest py-8">NO PUBLIC REFERENCES FOUND</div>
            ) : (
              <div className="space-y-3 max-h-[520px] overflow-y-auto pr-2">
                {result.findings.map((r, i) => (
                  <div key={i} className="border border-sentinel-border p-3">
                    <a href={r.url} target="_blank" rel="noreferrer" className="text-xs text-sentinel-cyan underline decoration-dotted hover:text-sentinel-neon">
                      {r.title || r.url}
                    </a>
                    <div className="mt-1 text-[9px] tracking-widest text-sentinel-muted uppercase">
                      {r.matched_query} // {r.source_type} // {r.source} // {r.published_at || 'n/d'}
                    </div>
                    {r.snippet && <p className="mt-1.5 text-[10px] text-sentinel-muted/80 leading-relaxed">{r.snippet}</p>}
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="PLATFORM REVIEW LINKS" className="lg:col-span-3">
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {(result.platform_leads || []).map((p) => (
                <a key={p.platform} href={p.search_url} target="_blank" rel="noreferrer" className="border border-sentinel-border p-3 hover:border-sentinel-neon hover:shadow-neon transition-colors">
                  <div className="text-sm text-sentinel-neon tracking-widest">{p.platform}</div>
                  <div className="text-[9px] text-sentinel-muted uppercase tracking-widest mt-1">{p.category} // manual review</div>
                </a>
              ))}
            </div>
          </Panel>
        </div>
      )}
    </div>
  )
}

function Input({ label, value, onChange, placeholder }) {
  return (
    <label className="block">
      <div className="text-[10px] tracking-[0.25em] text-sentinel-muted uppercase mb-1.5">{label}</div>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-black/60 border border-sentinel-border px-4 py-3 text-sm text-sentinel-neon tracking-wider focus:border-sentinel-neon focus:shadow-neon outline-none placeholder:text-sentinel-muted"
      />
    </label>
  )
}
