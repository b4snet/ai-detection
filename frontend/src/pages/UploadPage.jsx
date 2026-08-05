import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useSentinel } from '../context/SentinelContext.jsx'
import SystemLog from '../components/SystemLog.jsx'

const STAGES = [
  'INITIALIZING SECURE CHANNEL',
  'IMAGE RECEIVED // HASHING EVIDENCE',
  'COMPUTER VISION PROCESSING',
  'ENTITY RECOGNITION',
  'OSINT RETRIEVAL // PUBLIC SOURCES',
  'KNOWLEDGE GRAPH CONSTRUCTION',
  'AI REPORT GENERATION',
  'ARCHIVING INTELLIGENCE PRODUCT',
]

export default function UploadPage() {
  const [dragOver, setDragOver] = useState(false)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [status, setStatus] = useState('idle') // idle | uploading | processing | error
  const [analysisId, setAnalysisId] = useState(null)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const inputRef = useRef(null)
  const pollRef = useRef(null)
  const navigate = useNavigate()
  const { refreshAll } = useSentinel()

  const onFile = useCallback((f) => {
    if (!f) return
    if (!/image\/(png|jpe?g|webp|bmp|tiff?)/.test(f.type) && !/\.(png|jpe?g|webp|bmp|tif|tiff)$/i.test(f.name)) {
      setError('Unsupported file type. Use JPG/PNG/WEBP/BMP/TIFF.')
      return
    }
    setFile(f)
    setError('')
    setStatus('idle')
    setProgress(0)
    const reader = new FileReader()
    reader.onload = () => setPreview(reader.result)
    reader.readAsDataURL(f)
  }, [])

  useEffect(() => {
    if (status !== 'uploading') return
    ;(async () => {
      try {
        const res = await api.upload(file)
        setAnalysisId(res.id)
        setStatus('processing')
        setProgress(8)
        refreshAll()
      } catch (e) {
        setStatus('error')
        setError(String(e.message || e))
      }
    })()
  }, [status, file, refreshAll])

  // Poll analysis + advance progress animation during processing
  useEffect(() => {
    if (status !== 'processing' || !analysisId) return
    let phase = 0
    pollRef.current = setInterval(async () => {
      try {
        const a = await api.analysis(analysisId)
        setProgress((p) => Math.min(96, p + 4))
        if (a.status === 'complete') {
          clearInterval(pollRef.current)
          setProgress(100)
          refreshAll()
          setTimeout(() => navigate(`/analysis/${analysisId}`), 900)
        } else if (a.status === 'error') {
          clearInterval(pollRef.current)
          setStatus('error')
          setError('Intelligence pipeline failed. See system log.')
        }
      } catch {
        // keep polling
      }
      phase++
    }, 1400)
    return () => clearInterval(pollRef.current)
  }, [status, analysisId, navigate, refreshAll])

  useEffect(() => {
    if (status === 'processing') {
      const t = setInterval(() => {
        setProgress((p) => (p < 96 ? p + 1 : p))
      }, 260)
      return () => clearInterval(t)
    }
  }, [status])

  const stageIndex = Math.min(
    STAGES.length - 1,
    Math.floor((progress / 100) * STAGES.length),
  )

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-2xl md:text-3xl font-extrabold tracking-[0.3em] text-sentinel-neon glow-text">
          IMAGE INTELLIGENCE
        </h1>
        <p className="mt-2 text-[10px] tracking-[0.4em] text-sentinel-muted uppercase">
          Upload evidence for automated AI analysis
        </p>
      </div>

      {status === 'idle' || status === 'error' ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); onFile(e.dataTransfer.files?.[0]) }}
          onClick={() => inputRef.current?.click()}
          className={`cursor-pointer border-2 border-dashed p-12 md:p-20 text-center transition-all
            ${dragOver
              ? 'border-sentinel-neon bg-sentinel-neon/10 shadow-neon-lg'
              : 'border-sentinel-border bg-sentinel-panel/60 hover:border-sentinel-neon/70'}`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => onFile(e.target.files?.[0])}
          />
          {!preview ? (
            <>
              <div className="text-5xl text-sentinel-neon mb-4 animate-pulseglow">⇪</div>
              <div className="text-sm tracking-[0.3em] text-sentinel-neon">
                UPLOAD IMAGE FOR ANALYSIS
              </div>
              <div className="mt-3 text-[10px] tracking-widest text-sentinel-muted">
                PERSON // VEHICLE // OBJECT // LOCATION // DOCUMENT // SCREENSHOT // NEWS IMAGE
              </div>
              <div className="mt-6 text-[9px] text-sentinel-amber tracking-widest">
                DEMO SAMPLES: /backend/sample_data/sample_demo_incident.jpg
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center gap-4">
              <img src={preview} alt="preview" className="max-h-72 border border-sentinel-neon/50 shadow-neon" />
              <div className="text-xs text-sentinel-text">{file.name}</div>
              <div className="flex gap-3">
                <button
                  onClick={(e) => { e.stopPropagation(); setStatus('uploading') }}
                  className="btn-neon"
                >
                  ⚡ ANALYZE IMAGE
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null); setPreview(null) }}
                  className="border border-sentinel-border text-sentinel-muted px-4 py-2 text-xs tracking-widest hover:border-sentinel-red hover:text-sentinel-red"
                >
                  CANCEL
                </button>
              </div>
            </div>
          )}
        </div>
      ) : status === 'processing' ? (
        <div className="panel corner-frame p-8">
          <div className="text-center">
            <div className="relative mx-auto h-28 w-28">
              <div className="absolute inset-0 rounded-full border-2 border-sentinel-neon/20 animate-spinSlow" />
              <div className="absolute inset-2 rounded-full border-2 border-dashed border-sentinel-neon animate-spinSlow" style={{ animationDirection: 'reverse' }} />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sentinel-neon animate-pulseglow text-2xl">◎</span>
              </div>
            </div>
            <h2 className="mt-5 text-sm tracking-[0.3em] text-sentinel-neon glow-text">
              {STAGES[stageIndex]}
            </h2>
            <p className="mt-2 text-[10px] tracking-widest text-sentinel-muted">
              AI SCANNING EFFECT // MULTI-STAGE PIPELINE ACTIVE
            </p>

            {/* scan bar */}
            <div className="mt-6 mx-auto max-w-md">
              <div className="h-1.5 bg-sentinel-panel2 border border-sentinel-border relative overflow-hidden">
                <div
                  className="absolute inset-y-0 left-0 bg-sentinel-neon transition-all duration-300"
                  style={{ width: `${progress}%`, boxShadow: '0 0 10px rgba(0,255,136,0.7)' }}
                />
              </div>
              <div className="mt-2 flex justify-between text-[9px] tracking-widest text-sentinel-muted">
                <span>EXTRACTION</span>
                <span className="text-sentinel-neon">{progress}%</span>
              </div>
            </div>

            <div className="mt-5 text-[10px] tracking-widest text-sentinel-cyan animate-blink">
              ANALYZING://{file.name} ▊
            </div>
          </div>
        </div>
      ) : null}

      {error && (
        <div className="border border-sentinel-red text-sentinel-red text-xs px-4 py-3 tracking-widest">
          ⚠ {error}
        </div>
      )}

      {status === 'processing' && (
        <div>
          <div className="panel-title mb-2">LIVE PIPELINE FEED</div>
          <SystemLog height="h-56" />
        </div>
      )}
    </div>
  )
}
