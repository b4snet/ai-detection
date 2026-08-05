import { useCallback, useEffect, useRef, useState } from 'react'

const COLORS = {
  person: '#00ff88',
  organization: '#ffc857',
  location: '#35e0ff',
  vehicle: '#a78bfa',
  object: '#f0abfc',
  source: '#5d8a70',
  event: '#ff3355',
  analysis: '#00ff88',
}

const NODE_RADIUS = { person: 9, organization: 8, source: 5, event: 6, vehicle: 7, default: 6 }

let _edgesCache = []

/**
 * Force-directed knowledge graph rendered on 2D canvas.
 * Pan (drag empty space), zoom (wheel), hover (highlight), click (details).
 */
export default function KnowledgeGraph({ graph, height = 460 }) {
  const canvasRef = useRef(null)
  const [selected, setSelected] = useState(null)
  const [hovered, setHovered] = useState(null)

  const nodesRef = useRef([])
  const edgesRef = useRef([])
  const draggingRef = useRef(null)
  const viewRef = useRef({ x: 0, y: 0, k: 1 })

  const layout = useCallback(() => {
    const { nodes, edges } = graph || { nodes: [], edges: [] }
    if (!nodes.length) return
    const W = 1000
    const H = 600
    const n = nodes.map((nd, i) => {
      const angle = (i / Math.max(nodes.length, 1)) * Math.PI * 2
      const radius = Math.min(W, H) * 0.32
      return {
        id: nd.id,
        label: nd.label,
        node_type: nd.node_type,
        size: (NODE_RADIUS[nd.node_type] || NODE_RADIUS.default) * nd.size,
        x: W / 2 + radius * Math.cos(angle) + (Math.random() - 0.5) * 60,
        y: H / 2 + radius * Math.sin(angle) + (Math.random() - 0.5) * 60,
        vx: 0, vy: 0,
      }
    })
    const byId = new Map(n.map((x) => [x.id, x]))
    const e = (edges || [])
      .map((ed) => {
        const s = byId.get(ed.source)
        const t = byId.get(ed.target)
        if (!s || !t) return null
        return { ...ed, source: s, target: t }
      })
      .filter(Boolean)
    nodesRef.current = n
    edgesRef.current = e
    _edgesCache = e
  }, [graph])

  useEffect(() => {
    layout()
  }, [layout])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    let raf = 0
    let mouse = { x: -999, y: -999 }

    const resize = () => {
      canvas.width = canvas.clientWidth * dpr
      canvas.height = canvas.clientHeight * dpr
    }
    resize()
    window.addEventListener('resize', resize)

    const step = () => {
      const nodes = nodesRef.current
      const edges = edgesRef.current
      // force simulation (repulsion + spring + centering)
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i]
          const b = nodes[j]
          let dx = a.x - b.x
          let dy = a.y - b.y
          let d = Math.sqrt(dx * dx + dy * dy) || 1
          const force = 9000 / (d * d)
          dx /= d; dy /= d
          a.vx += dx * force * 0.6
          a.vy += dy * force * 0.6
          b.vx -= dx * force * 0.6
          b.vy -= dy * force * 0.6
        }
      }
      for (const e of edges) {
        const dx = e.target.x - e.source.x
        const dy = e.target.y - e.source.y
        const d = Math.sqrt(dx * dx + dy * dy) || 1
        const ideal = 110
        const f = (d - ideal) * 0.02
        e.source.vx += (dx / d) * f
        e.source.vy += (dy / d) * f
        e.target.vx -= (dx / d) * f
        e.target.vy -= (dy / d) * f
      }
      for (const nd of nodes) {
        nd.vx *= 0.85
        nd.vy *= 0.85
        nd.x += nd.vx
        nd.y += nd.vy
        nd.x = Math.max(30, Math.min(970, nd.x))
        nd.y = Math.max(30, Math.min(570, nd.y))
      }
      draw(ctx, dpr, nodes, edges, mouse)
      raf = requestAnimationFrame(step)
    }

    const draw = (ctx, dpr, nodes, edges, mouse) => {
      const { x: vx, y: vy, k } = viewRef.current
      const W = canvas.width
      const H = canvas.height
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, W / dpr, H / dpr)

      // edges
      for (const e of edges) {
        const inPath = hovered && (e.source.id === hovered.id || e.target.id === hovered.id)
        ctx.strokeStyle = inPath ? 'rgba(0,255,136,0.8)' : 'rgba(0,255,136,0.14)'
        ctx.lineWidth = inPath ? 1.6 : (0.7 * e.weight) || 0.7
        ctx.beginPath()
        ctx.moveTo(e.source.x * k + vx, e.source.y * k + vy)
        ctx.lineTo(e.target.x * k + vx, e.target.y * k + vy)
        ctx.stroke()
      }

      // nodes
      for (const nd of nodes) {
        const px = nd.x * k + vx
        const py = nd.y * k + vy
        const r = nd.size * k
        const active = hovered && hovered.id === nd.id
        ctx.beginPath()
        ctx.arc(px, py, r + (active ? 4 : 0), 0, Math.PI * 2)
        ctx.fillStyle = COLORS[nd.node_type] || COLORS.default
        ctx.globalAlpha = 0.12
        ctx.fill()
        ctx.globalAlpha = 1
        ctx.strokeStyle = COLORS[nd.node_type] || COLORS.default
        ctx.lineWidth = active ? 2 : 1
        ctx.stroke()
        ctx.fillStyle = COLORS[nd.node_type] || COLORS.default
        ctx.beginPath()
        ctx.arc(px, py, Math.max(2, r * 0.4), 0, Math.PI * 2)
        ctx.fill()
        // label
        ctx.font = '600 9px JetBrains Mono, monospace'
        ctx.textAlign = 'center'
        ctx.fillStyle = active ? '#00ff88' : '#8fd6ab'
        ctx.fillText(short(nd.label, 22), px, py - r - 6)
      }
    }

    const toWorld = (clientX, clientY) => {
      const rect = canvas.getBoundingClientRect()
      const { x: vx, y: vy, k } = viewRef.current
      return { x: (clientX - rect.left - vx) / k, y: (clientY - rect.top - vy) / k }
    }

    const onPointerDown = (ev) => {
      const { x, y } = toWorld(ev.clientX, ev.clientY)
      const nd = nodesRef.current.find((n) => {
        const dx = n.x - x, dy = n.y - y
        return Math.sqrt(dx * dx + dy * dy) < 14
      })
      if (nd) {
        draggingRef.current = { node: nd, mx: ev.clientX, my: ev.clientY }
        setSelected(nd)
      } else {
        draggingRef.current = { node: null, mx: ev.clientX, my: ev.clientY }
        setSelected(null)
      }
    }
    const onPointerMove = (ev) => {
      mouse = { x: ev.clientX, y: ev.clientY }
      const { x, y } = toWorld(ev.clientX, ev.clientY)
      const nd = nodesRef.current.find((n) => {
        const dx = n.x - x, dy = n.y - y
        return Math.sqrt(dx * dx + dy * dy) < 14
      })
      setHovered(nd || null)
      if (draggingRef.current) {
        const { node, mx, my } = draggingRef.current
        if (node) {
          node.x += (ev.clientX - mx) / (viewRef.current.k || 1)
          node.y += (ev.clientY - my) / (viewRef.current.k || 1)
          draggingRef.current.mx = ev.clientX
          draggingRef.current.my = ev.clientY
        } else {
          viewRef.current.x += ev.clientX - mx
          viewRef.current.y += ev.clientY - my
          draggingRef.current.mx = ev.clientX
          draggingRef.current.my = ev.clientY
        }
      }
    }
    const onPointerUp = () => { draggingRef.current = null }
    const onWheel = (ev) => {
      ev.preventDefault()
      const v = viewRef.current
      const factor = ev.deltaY < 0 ? 1.1 : 0.9
      v.k = Math.max(0.35, Math.min(2.4, v.k * factor))
    }
    const onLeave = () => setHovered(null)

    canvas.addEventListener('pointerdown', onPointerDown)
    canvas.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
    canvas.addEventListener('wheel', onWheel, { passive: false })
    canvas.addEventListener('pointerleave', onLeave)

    raf = requestAnimationFrame(step)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointerup', onPointerUp)
      canvas.removeEventListener('pointerdown', onPointerDown)
      canvas.removeEventListener('pointermove', onPointerMove)
      canvas.removeEventListener('wheel', onWheel)
      canvas.removeEventListener('pointerleave', onLeave)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const related = hovered || selected

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        className="w-full border border-sentinel-border bg-black/50"
        style={{ height: `${height}px`, cursor: draggingRef.current ? 'grabbing' : 'grab' }}
      />
      <div className="absolute top-2 left-2 text-[9px] tracking-[0.25em] text-sentinel-muted pointer-events-none">
        DRAG ▸ NAVIGATE&nbsp;&nbsp;//&nbsp;&nbsp;WHEEL ▸ ZOOM
      </div>
      <div className="absolute top-2 right-2 flex flex-wrap gap-2 pointer-events-none">
        {Object.entries(COLORS).map(([k, c]) => (
          <span key={k} className="flex items-center gap-1 text-[9px] tracking-widest" style={{ color: c }}>
            <span className="h-2 w-2 rounded-full" style={{ background: c }} /> {k.toUpperCase()}
          </span>
        ))}
      </div>
      {related && (
        <div className="absolute bottom-2 left-2 border border-sentinel-border bg-sentinel-bg/90 px-3 py-2 text-[11px] max-w-[60%]">
          <div className="text-sentinel-neon tracking-widest font-semibold">
            {related.label}
          </div>
          <div className="text-sentinel-muted tracking-widest mt-0.5">
            TYPE: {related.node_type.toUpperCase()}
          </div>
          <div className="text-sentinel-muted mt-1">
            {edgesRelated(related).map((e) => (
              <div key={e.source.id + e.target.id}>
                ↔ {e.relation}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function edgesRelated(node) {
  return _edgesCache.filter(
    (e) => e.source.id === node.id || e.target.id === node.id,
  )
}

function short(s, n) {
  return s && s.length > n ? s.slice(0, n - 1) + '…' : s
}
