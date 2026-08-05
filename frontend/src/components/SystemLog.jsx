import { useEffect, useRef } from 'react'
import { useSentinel } from '../context/SentinelContext.jsx'

const LEVEL_COLOR = {
  INFO: 'text-sentinel-neon',
  WARNING: 'text-sentinel-amber',
  ERROR: 'text-sentinel-red',
  SUCCESS: 'text-sentinel-cyan',
}

/** Terminal-style scrolling log viewer. Auto-follows newest lines. */
export default function SystemLog({ height = 'h-64' }) {
  const { logs } = useSentinel()
  const boxRef = useRef(null)

  useEffect(() => {
    const el = boxRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logs])

  return (
    <div
      ref={boxRef}
      className={`${height} overflow-y-auto bg-black/60 border border-sentinel-border p-3 text-[11px] leading-relaxed`}
    >
      {logs.length === 0 && (
        <div className="text-sentinel-muted animate-blink">_ waiting for signal...</div>
      )}
      {logs.map((l) => {
        const time = (l.timestamp || '').slice(11, 19)
        return (
          <div key={l.id} className="flex gap-2">
            <span className="text-sentinel-muted shrink-0">[{time}]</span>
            <span className={`shrink-0 w-14 ${LEVEL_COLOR[l.level] || 'text-sentinel-muted'}`}>
              {l.level}
            </span>
            <span className="text-sentinel-text/90 break-all">{l.message}</span>
          </div>
        )
      })}
      <div className="text-sentinel-neon animate-blink mt-1">▊</div>
    </div>
  )
}
