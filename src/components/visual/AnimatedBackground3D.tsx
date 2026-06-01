import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function ParticleField() {
  const ref = useRef<THREE.Points>(null)

  // Generate particle positions
  const particlesPosition = useMemo(() => {
    const positions = new Float32Array(2000 * 3)

    for (let i = 0; i < 2000; i++) {
      const i3 = i * 3
      positions[i3] = (Math.random() - 0.5) * 10
      positions[i3 + 1] = (Math.random() - 0.5) * 10
      positions[i3 + 2] = (Math.random() - 0.5) * 10
    }

    return positions
  }, [])

  // Animate particles
  useFrame((state) => {
    if (!ref.current) return

    const time = state.clock.getElapsedTime()
    ref.current.rotation.x = time * 0.05
    ref.current.rotation.y = time * 0.075
  })

  return (
    <Points ref={ref} positions={particlesPosition} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#06B6D4"
        size={0.02}
        sizeAttenuation={true}
        depthWrite={false}
        opacity={0.6}
      />
    </Points>
  )
}

function AnimatedMesh() {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (!meshRef.current) return

    const time = state.clock.getElapsedTime()
    meshRef.current.rotation.x = time * 0.1
    meshRef.current.rotation.y = time * 0.15
    meshRef.current.position.y = Math.sin(time * 0.5) * 0.5
  })

  return (
    <mesh ref={meshRef} position={[0, 0, 0]}>
      <torusKnotGeometry args={[1, 0.3, 128, 16]} />
      <meshStandardMaterial
        color="#14B8A6"
        wireframe
        transparent
        opacity={0.2}
      />
    </mesh>
  )
}

function FloatingShapes() {
  const shapes = useMemo(() => {
    return Array.from({ length: 5 }, () => ({
      position: [
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8,
        (Math.random() - 0.5) * 8,
      ] as [number, number, number],
      scale: Math.random() * 0.5 + 0.3,
      speed: Math.random() * 0.5 + 0.5,
      offset: Math.random() * Math.PI * 2,
    }))
  }, [])

  return (
    <>
      {shapes.map((shape, i) => (
        <FloatingShape key={i} {...shape} />
      ))}
    </>
  )
}

function FloatingShape({
  position,
  scale,
  speed,
  offset
}: {
  position: [number, number, number]
  scale: number
  speed: number
  offset: number
}) {
  const meshRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (!meshRef.current) return

    const time = state.clock.getElapsedTime()
    meshRef.current.position.y = position[1] + Math.sin(time * speed + offset) * 0.5
    meshRef.current.rotation.x = time * 0.2
    meshRef.current.rotation.z = time * 0.1
  })

  return (
    <mesh ref={meshRef} position={position} scale={scale}>
      <octahedronGeometry args={[1, 0]} />
      <meshStandardMaterial
        color="#2563EB"
        wireframe
        transparent
        opacity={0.15}
      />
    </mesh>
  )
}

interface AnimatedBackground3DProps {
  className?: string
}

export default function AnimatedBackground3D({ className = '' }: AnimatedBackground3DProps) {
  // Check for reduced motion preference
  const prefersReducedMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  if (prefersReducedMotion) {
    // Return static gradient background if reduced motion is preferred
    return (
      <div
        className={`absolute inset-0 bg-gradient-to-br from-fintech-navy via-fintech-navy-light to-fintech-navy ${className}`}
      />
    )
  }

  return (
    <div className={`absolute inset-0 ${className}`} style={{ pointerEvents: 'none' }}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 75 }}
        gl={{
          antialias: false,
          alpha: true,
          powerPreference: 'high-performance'
        }}
        dpr={[1, 1.5]}
        style={{ pointerEvents: 'none' }}
      >
        <color attach="background" args={['#0A1628']} />

        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#06B6D4" />

        {/* 3D Elements */}
        <ParticleField />
        <AnimatedMesh />
        <FloatingShapes />
      </Canvas>

      {/* Gradient overlay for depth */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-fintech-navy/50 to-fintech-navy pointer-events-none" />
    </div>
  )
}
