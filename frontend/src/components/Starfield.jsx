import { useEffect, useRef } from 'react'
import * as THREE from 'three'

/**
 * Three.js animated particle field + drifting wireframe globe.
 * Pure visual layer — sits behind all content (z-0).
 */
export default function Starfield() {
  const mountRef = useRef(null)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(
      60, mount.clientWidth / mount.clientHeight, 0.1, 1200,
    )
    camera.position.z = 160

    const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true })
    renderer.setSize(mount.clientWidth, mount.clientHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
    mount.appendChild(renderer.domElement)

    // Particle field
    const particleCount = 900
    const positions = new Float32Array(particleCount * 3)
    for (let i = 0; i < particleCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 700
      positions[i + 1] = (Math.random() - 0.5) * 700
      positions[i + 2] = (Math.random() - 0.5) * 700
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    const mat = new THREE.PointsMaterial({
      color: 0x00ff88,
      size: 0.55,
      transparent: true,
      opacity: 0.55,
      depthWrite: false,
    })
    const points = new THREE.Points(geo, mat)
    scene.add(points)

    // Wireframe globe for the orbital aesthetic
    const globeGeo = new THREE.SphereGeometry(70, 22, 22)
    const globeMat = new THREE.MeshBasicMaterial({
      color: 0x0b1f18,
      wireframe: true,
      transparent: true,
      opacity: 0.22,
    })
    const globe = new THREE.Mesh(globeGeo, globeMat)
    globe.position.set(0, 0, -60)
    scene.add(globe)

    // Equatorial ring
    const ringGeo = new THREE.RingGeometry(78, 82, 64)
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x00ff88,
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide,
    })
    const ring = new THREE.Mesh(ringGeo, ringMat)
    ring.rotation.x = Math.PI / 2.2
    ring.position.z = -60
    scene.add(ring)

    let raf = 0
    const clock = new THREE.Clock()
    const animate = () => {
      const t = clock.getElapsedTime()
      points.rotation.y = t * 0.012
      globe.rotation.y = t * 0.02
      globe.rotation.x = t * 0.008
      ring.rotation.z = t * 0.01
      renderer.render(scene, camera)
      raf = requestAnimationFrame(animate)
    }
    animate()

    const onResize = () => {
      camera.aspect = mount.clientWidth / mount.clientHeight
      camera.updateProjectionMatrix()
      renderer.setSize(mount.clientWidth, mount.clientHeight)
    }
    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', onResize)
      geo.dispose()
      mat.dispose()
      globeGeo.dispose()
      globeMat.dispose()
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [])

  return <div ref={mountRef} className="fixed inset-0 z-0 opacity-70" aria-hidden="true" />
}
