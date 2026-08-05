import { useState } from 'react'
import { api } from '../api/client'
import Panel from '../components/Panel.jsx'

const demoProfiles = [
  {
    id: 'np-demo-001',
    name: 'Aarav Sharma',
    city: 'Kathmandu',
    district: 'Kathmandu',
    province: 'Bagmati',
    public_socials: {
      facebook: 'https://facebook.com/demo-aarav-sharma',
      instagram: 'https://instagram.com/demo_aarav',
      linkedin: 'https://linkedin.com/in/demo-aarav-sharma',
    },
  },
  {
    id: 'np-demo-002',
    name: 'Sita Gurung',
    city: 'Pokhara',
    district: 'Kaski',
    province: 'Gandaki',
    public_socials: {
      facebook: 'https://facebook.com/demo-sita-gurung',
      instagram: 'https://instagram.com/demo_sita',
      linkedin: 'https://linkedin.com/in/demo-sita-gurung',
    },
  },
]

function demoMatch(file) {
  const seed = (file?.name || 'demo').split('').reduce((n, c) => n + c.charCodeAt(0), 0)
  const matches = demoProfiles.map((profile, i) => ({
    profile,
    confidence: 0.55 + (((seed + i * 31) % 30) / 100),
    method: 'browser_demo_no_backend',
    verification: 'DEMO RESULT - ADD AUTHORIZED NEPAL DATASET FOR REAL MATCHING',
  })).sort((a, b) => b.confidence - a.confidence)
  return {
    scope: 'Browser demo only',
    notice: 'This is a static Netlify demo. Real matching requires the FastAPI backend and consent-based enrolled Nepal profiles.',
    uploaded_image: '',
    matches,
  }
}

export default function NepalMatcherPage() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const choose = (f) => {
    setFile(f)
    setResult(null)
    setError('')
    setPreview(f ? URL.createObjectURL(f) : '')
  }

  const run = async (e) => {
    e.preventDefault()
    if (!file) return setError('Upload an image first.')
    setLoading(true)
    setError('')
    try {
      setResult(await api.directoryMatch(file))
    } catch (err) {
      setResult(demoMatch(file))
      setError('Backend not connected, showing browser demo. Host the FastAPI backend for real authorized-directory matching.')
    } finally {
      setLoading(false)
    }
  }

  const top = result?.matches?.[0]

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl md:text-5xl font-extrabold tracking-[0.18em] text-sentinel-neon glow-text">
          NEPAL IDENTITY MATCHER
        </h1>
        <p className="mt-3 text-xs tracking-[0.28em] text-sentinel-muted uppercase">
          Upload image → closest authorized directory match → public socials + city
        </p>
      </div>

      <Panel title="UPLOAD PERSON IMAGE">
        <form onSubmit={run} className="grid md:grid-cols-[280px_1fr] gap-5 items-center">
          <label className="h-72 border border-dashed border-sentinel-neon/60 bg-black/50 flex items-center justify-center cursor-pointer hover:shadow-neon transition">
            {preview ? (
              <img src={preview} className="h-full w-full object-cover" />
            ) : (
              <span className="text-sentinel-muted text-xs tracking-widest text-center px-5">
                CLICK TO SELECT JPG/PNG IMAGE
              </span>
            )}
            <input type="file" accept="image/*" className="hidden" onChange={(e) => choose(e.target.files?.[0])} />
          </label>

          <div className="space-y-4">
            <div className="border border-sentinel-amber/50 bg-sentinel-amber/5 p-4 text-xs text-sentinel-muted leading-relaxed">
              This matches only against your authorized Nepal profile database. It does not scrape the internet or identify random people. Add consent-based profiles in <span className="text-sentinel-cyan">backend/sample_data/authorized_nepal_profiles.json</span>.
            </div>
            <button className="btn-neon disabled:opacity-50" disabled={loading || !file}>
              {loading ? 'MATCHING...' : 'FIND CLOSEST MATCH'}
            </button>
            {error && <div className="text-sentinel-red text-xs tracking-widest">⚠ {error}</div>}
          </div>
        </form>
      </Panel>

      {top && (
        <Panel title="CLOSEST MATCH">
          <div className="grid md:grid-cols-[1fr_220px] gap-5">
            <div>
              <div className="text-3xl font-black text-sentinel-neon tracking-widest">{top.profile.name}</div>
              <div className="mt-2 text-sm text-sentinel-cyan tracking-widest">
                {top.profile.city}, {top.profile.district} · {top.profile.province}
              </div>
              <div className="mt-4 text-xs text-sentinel-muted tracking-widest">
                CONFIDENCE: <span className="text-sentinel-amber">{Math.round(top.confidence * 100)}%</span>
              </div>
              <div className="mt-1 text-[10px] text-sentinel-muted uppercase tracking-widest">{top.verification}</div>
              <div className="mt-5 grid sm:grid-cols-3 gap-3">
                {Object.entries(top.profile.public_socials || {}).map(([name, url]) => (
                  <a key={name} href={url} target="_blank" rel="noreferrer" className="border border-sentinel-border p-3 text-center hover:border-sentinel-neon hover:shadow-neon">
                    <div className="text-sentinel-neon uppercase tracking-widest text-xs">{name}</div>
                    <div className="text-[9px] text-sentinel-muted mt-1 truncate">OPEN PROFILE</div>
                  </a>
                ))}
              </div>
            </div>
            <div className="border border-sentinel-border p-4 text-[10px] text-sentinel-muted leading-relaxed">
              <div className="text-sentinel-amber tracking-widest mb-2">IMPORTANT</div>
              {result.notice}
              <br /><br />Method: {top.method}
            </div>
          </div>
        </Panel>
      )}

      {result?.matches?.length > 1 && (
        <Panel title="OTHER POSSIBLE MATCHES">
          <div className="space-y-2">
            {result.matches.slice(1).map((m) => (
              <div key={m.profile.id} className="flex justify-between border border-sentinel-border p-3 text-xs">
                <span className="text-sentinel-cyan">{m.profile.name} · {m.profile.city}</span>
                <span className="text-sentinel-amber">{Math.round(m.confidence * 100)}%</span>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  )
}
