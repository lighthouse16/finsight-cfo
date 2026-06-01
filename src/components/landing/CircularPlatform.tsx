import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

export default function CircularPlatform() {
  const ring1Ref = useRef<THREE.Mesh>(null)
  const ring2Ref = useRef<THREE.Mesh>(null)
  const ring3Ref = useRef<THREE.Mesh>(null)
  const ring4Ref = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    const time = state.clock.elapsedTime
    
    if (ring1Ref.current) {
      ring1Ref.current.rotation.z = time * 0.1
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.z = -time * 0.15
    }
    if (ring3Ref.current) {
      ring3Ref.current.rotation.z = time * 0.08
    }
    if (ring4Ref.current) {
      ring4Ref.current.rotation.z = -time * 0.12
    }
  })

  return (
    <group position={[0, -1.5, 0]}>
      {/* Base platform */}
      <mesh position={[0, 0, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[4, 4, 0.1, 64]} />
        <meshStandardMaterial
          color="#0ea5e9"
          transparent
          opacity={0.1}
          emissive="#0ea5e9"
          emissiveIntensity={0.2}
        />
      </mesh>

      {/* Ring 1 - Innermost */}
      <mesh ref={ring1Ref} position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.5, 1.7, 64]} />
        <meshStandardMaterial
          color="#06b6d4"
          transparent
          opacity={0.6}
          emissive="#06b6d4"
          emissiveIntensity={1.5}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Ring 2 */}
      <mesh ref={ring2Ref} position={[0, 0.08, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.0, 2.15, 64]} />
        <meshStandardMaterial
          color="#0ea5e9"
          transparent
          opacity={0.5}
          emissive="#0ea5e9"
          emissiveIntensity={1.2}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Ring 3 */}
      <mesh ref={ring3Ref} position={[0, 0.11, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.5, 2.6, 64]} />
        <meshStandardMaterial
          color="#0284c7"
          transparent
          opacity={0.4}
          emissive="#0284c7"
          emissiveIntensity={1.0}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Ring 4 - Outermost */}
      <mesh ref={ring4Ref} position={[0, 0.14, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[3.0, 3.1, 64]} />
        <meshStandardMaterial
          color="#0369a1"
          transparent
          opacity={0.3}
          emissive="#0369a1"
          emissiveIntensity={0.8}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Tech grid lines */}
      {[...Array(8)].map((_, i) => {
        const angle = (i / 8) * Math.PI * 2
        const x = Math.cos(angle) * 3.5
        const z = Math.sin(angle) * 3.5
        return (
          <mesh
            key={i}
            position={[x / 2, 0.15, z / 2]}
            rotation={[-Math.PI / 2, 0, angle]}
          >
            <planeGeometry args={[0.02, 3.5]} />
            <meshBasicMaterial
              color="#06b6d4"
              transparent
              opacity={0.3}
            />
          </mesh>
        )
      })}

      {/* Circular grid */}
      {[1, 1.5, 2, 2.5, 3, 3.5].map((radius, i) => (
        <mesh
          key={`circle-${i}`}
          position={[0, 0.16, 0]}
          rotation={[-Math.PI / 2, 0, 0]}
        >
          <ringGeometry args={[radius - 0.01, radius + 0.01, 64]} />
          <meshBasicMaterial
            color="#06b6d4"
            transparent
            opacity={0.2}
          />
        </mesh>
      ))}

      {/* Point lights for glow */}
      <pointLight position={[0, 0.5, 0]} intensity={2} color="#0ea5e9" distance={5} />
      <pointLight position={[2, 0.2, 2]} intensity={1} color="#06b6d4" distance={3} />
      <pointLight position={[-2, 0.2, -2]} intensity={1} color="#06b6d4" distance={3} />
    </group>
  )
}
