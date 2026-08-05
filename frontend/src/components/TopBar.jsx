import { NavLink } from 'react-router-dom'
import { useSentinel } from '../context/SentinelContext.jsx'

const links = [
  { to: '/', label: 'MATCHER', icon: '◎' },
  { to: '/footprint', label: 'MANUAL AUDIT', icon: '⌁' },
  { to: '/logs', label: 'LOG', icon: '≣' },
]

function StatusDot({ online }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`h-2 w-2 rounded-full ${online ? 'bg-sentinel-neon animate-pulseglow shadow-neon' : 'bg-sentinel-red animate-blink'}`}
      />
      <span className="text-[10px] tracking-[0.25em]">{online ? 'ONLINE' : 'DEGRADED'}</span>
    </span>
  )
}

export default function TopBar() {
  const { status } = useSentinel()

  return (
    <header className="fixed top-0 inset-x-0 z-40 border-b border-sentinel-border bg-sentinel-bg/85 backdrop-blur-md">
      <div className="max-w-[1500px] mx-auto px-4 md:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 border border-sentinel-neon flex items-center justify-center shadow-neon relative">
              <span className="text-sentinel-neon text-lg">◉</span>
            </div>
            <div>
              <div className="font-extrabold tracking-[0.3em] text-sentinel-neon glow-text text-sm">
                NEPAL ID MATCHER
              </div>
              <div className="text-[9px] tracking-[0.35em] text-sentinel-muted">
                AUTHORIZED DIGITAL IDENTITY DIRECTORY
              </div>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-1">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 text-[11px] tracking-[0.2em] transition-colors
                   ${isActive
                     ? 'bg-sentinel-neon/10 text-sentinel-neon border-b border-sentinel-neon shadow-neon'
                     : 'text-sentinel-muted hover:text-sentinel-neon hover:bg-sentinel-neon/5'}`
                }
              >
                <span>{l.icon}</span>
                {l.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <StatusDot online={status?.status === 'ONLINE'} />
            <div className="hidden lg:block text-right">
              <div className="text-[9px] text-sentinel-muted tracking-widest">
                AI ENGINE
              </div>
              <div
                className={`text-[11px] tracking-widest ${status?.ollama_online ? 'text-sentinel-neon' : 'text-sentinel-amber'}`}
              >
                {status?.ai_engine || '...'}
              </div>
            </div>
          </div>
        </div>

        {/* mobile nav */}
        <nav className="md:hidden flex overflow-x-auto gap-1 pb-2">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              className={({ isActive }) =>
                `px-3 py-1.5 text-[10px] tracking-widest whitespace-nowrap border
                 ${isActive ? 'border-sentinel-neon text-sentinel-neon' : 'border-sentinel-border text-sentinel-muted'}`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  )
}
