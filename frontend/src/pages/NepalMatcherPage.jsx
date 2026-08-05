import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Panel from '../components/Panel.jsx'

const blank = { name: '', city: '', district: '', province: '', facebook: '', instagram: '', linkedin: '', website: '', notes: '', image: null }

export default function NepalMatcherPage() {
  const [tab, setTab] = useState('match')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [result, setResult] = useState(null)
  const [profiles, setProfiles] = useState([])
  const [form, setForm] = useState(blank)
  const [enrollPreview, setEnrollPreview] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const refresh = async () => {
    try { setProfiles((await api.directoryProfiles()).profiles || []) } catch { setProfiles([]) }
  }
  useEffect(() => { refresh() }, [])

  const choose = (f) => {
    setFile(f); setResult(null); setError(''); setPreview(f ? URL.createObjectURL(f) : '')
  }

  const run = async (e) => {
    e.preventDefault()
    if (!file) return setError('Upload an image first.')
    setLoading(true); setError(''); setResult(null)
    try { setResult(await api.directoryMatch(file)) }
    catch (err) { setError('Backend not connected or match failed. No fake results are shown. ' + String(err.message || err)) }
    finally { setLoading(false) }
  }

  const enroll = async (e) => {
    e.preventDefault()
    if (!form.image) return setError('Reference image is required.')
    if (!form.name.trim()) return setError('Name is required.')
    setLoading(true); setError(''); setMessage('')
    try {
      await api.directoryEnroll(form)
      setMessage('Profile enrolled successfully. Matching will now use this real authorized record.')
      setForm(blank); setEnrollPreview(''); await refresh(); setTab('match')
    } catch (err) { setError(String(err.message || err)) }
    finally { setLoading(false) }
  }

  const top = result?.matches?.[0]

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-3xl md:text-5xl font-extrabold tracking-[0.18em] text-sentinel-neon glow-text">NEPAL IDENTITY MATCHER</h1>
        <p className="mt-3 text-xs tracking-[0.28em] text-sentinel-muted uppercase">Real results only from enrolled authorized profiles</p>
      </div>

      <div className="flex gap-2 justify-center">
        {['match', 'enroll'].map((t) => <button key={t} onClick={() => { setTab(t); setError(''); setMessage('') }} className={`px-5 py-2 border text-xs tracking-widest ${tab === t ? 'border-sentinel-neon text-sentinel-neon shadow-neon' : 'border-sentinel-border text-sentinel-muted'}`}>{t === 'match' ? 'MATCH IMAGE' : 'ENROLL PROFILE'}</button>)}
      </div>

      {error && <div className="border border-sentinel-red text-sentinel-red text-xs px-4 py-3 tracking-widest">⚠ {error}</div>}
      {message && <div className="border border-sentinel-neon text-sentinel-neon text-xs px-4 py-3 tracking-widest">✓ {message}</div>}

      {tab === 'match' && <>
        <Panel title={`UPLOAD PERSON IMAGE · ${profiles.length} ENROLLED PROFILE(S)`}>
          <form onSubmit={run} className="grid md:grid-cols-[280px_1fr] gap-5 items-center">
            <ImageBox preview={preview} label="CLICK TO SELECT QUERY IMAGE" onChange={choose} />
            <div className="space-y-4">
              <div className="border border-sentinel-amber/50 bg-sentinel-amber/5 p-4 text-xs text-sentinel-muted leading-relaxed">
                No fake information is generated. If zero profiles are enrolled or the backend is offline, this will return no identity.
              </div>
              <button className="btn-neon disabled:opacity-50" disabled={loading || !file}>{loading ? 'MATCHING...' : 'FIND CLOSEST AUTHORIZED MATCH'}</button>
            </div>
          </form>
        </Panel>

        {result && !top && <Panel title="NO MATCH"><div className="text-sentinel-muted text-xs tracking-widest py-6">{result.notice || 'No enrolled authorized profiles matched.'}</div></Panel>}
        {top && <MatchResult result={result} top={top} />}
        {result?.matches?.length > 1 && <Panel title="OTHER POSSIBLE MATCHES"><div className="space-y-2">{result.matches.slice(1).map((m) => <div key={m.profile.id} className="flex justify-between border border-sentinel-border p-3 text-xs"><span className="text-sentinel-cyan">{m.profile.name} · {m.profile.city}</span><span className="text-sentinel-amber">{Math.round(m.confidence * 100)}%</span></div>)}</div></Panel>}
      </>}

      {tab === 'enroll' && <Panel title="ENROLL AUTHORIZED PROFILE">
        <form onSubmit={enroll} className="grid md:grid-cols-[260px_1fr] gap-5">
          <ImageBox preview={enrollPreview} label="REFERENCE PHOTO" onChange={(f) => { setForm({ ...form, image: f }); setEnrollPreview(f ? URL.createObjectURL(f) : '') }} />
          <div className="grid sm:grid-cols-2 gap-3">
            {['name', 'city', 'district', 'province', 'facebook', 'instagram', 'linkedin', 'website'].map((k) => <Input key={k} label={k} value={form[k]} onChange={(v) => setForm({ ...form, [k]: v })} />)}
            <label className="sm:col-span-2"><div className="label">notes / consent proof</div><input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="input" /></label>
            <button className="btn-neon sm:col-span-2 disabled:opacity-50" disabled={loading}>{loading ? 'ENROLLING...' : 'ENROLL PROFILE'}</button>
          </div>
        </form>
      </Panel>}
    </div>
  )
}

function ImageBox({ preview, label, onChange }) {
  return <label className="h-72 border border-dashed border-sentinel-neon/60 bg-black/50 flex items-center justify-center cursor-pointer hover:shadow-neon transition">{preview ? <img src={preview} className="h-full w-full object-cover" /> : <span className="text-sentinel-muted text-xs tracking-widest text-center px-5">{label}</span>}<input type="file" accept="image/*" className="hidden" onChange={(e) => onChange(e.target.files?.[0])} /></label>
}

function Input({ label, value, onChange }) {
  return <label><div className="label">{label}</div><input value={value} onChange={(e) => onChange(e.target.value)} className="input" /></label>
}

function MatchResult({ result, top }) {
  return <Panel title="CLOSEST MATCH"><div className="grid md:grid-cols-[1fr_220px] gap-5"><div><div className="text-3xl font-black text-sentinel-neon tracking-widest">{top.profile.name}</div><div className="mt-2 text-sm text-sentinel-cyan tracking-widest">{top.profile.city}, {top.profile.district} · {top.profile.province}</div><div className="mt-4 text-xs text-sentinel-muted tracking-widest">CONFIDENCE: <span className="text-sentinel-amber">{Math.round(top.confidence * 100)}%</span></div><div className="mt-1 text-[10px] text-sentinel-muted uppercase tracking-widest">{top.verification}</div><div className="mt-5 grid sm:grid-cols-3 gap-3">{Object.entries(top.profile.public_socials || {}).map(([name, url]) => url && <a key={name} href={url} target="_blank" rel="noreferrer" className="border border-sentinel-border p-3 text-center hover:border-sentinel-neon hover:shadow-neon"><div className="text-sentinel-neon uppercase tracking-widest text-xs">{name}</div><div className="text-[9px] text-sentinel-muted mt-1 truncate">OPEN PROFILE</div></a>)}</div></div><div className="border border-sentinel-border p-4 text-[10px] text-sentinel-muted leading-relaxed"><div className="text-sentinel-amber tracking-widest mb-2">IMPORTANT</div>{result.notice}<br /><br />Method: {top.method}</div></div></Panel>
}
