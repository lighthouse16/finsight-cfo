import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { RoundedBox, Text } from '@react-three/drei'
import * as THREE from 'three'

export default function FloatingCube() {
  const cubeRef = useRef<THREE.Mesh>(null)
  const groupRef = useRef<THREE.Group>(null)
  const innerGlowRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    const time = state.clock.elapsedTime
    
    if (cubeRef.current) {
      cubeRef.current.rotation.y = time * 0.2
      cubeRef.current.rotation.x = Math.sin(time * 0.3) * 0.05
    }
    if (groupRef.current) {
      groupRef.current.position.y = Math.sin(time * 0.5) * 0.15
    }
    if (innerGlowRef.current) {
      const pulse = 1 + Math.sin(time * 2) * 0.1
      innerGlowRef.current.scale.set(pulse, pulse, pulse)
    }
  })

  return (
    <group ref={groupRef} position={[0, 0.5, 0]}>
      {/* Multiple glow layers for stronger effect */}
      <mesh scale={1.4}>
        <boxGeometry args={[2, 2, 2]} />
        <meshBasicMaterial
          color="#0ea5e9"
          transparent
          opacity={0.05}
          side={THREE.BackSide}
        />
      </mesh>

      <mesh scale={1.2}>
        <boxGeometry args={[2, 2, 2]} />
        <meshBasicMaterial
          color="#06b6d4"
          transparent
          opacity={0.1}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Main Glass Cube - More visible */}
      <RoundedBox ref={cubeRef} args={[1.8, 1.8, 1.8]} radius={0.12} smoothness={4}>
        <meshPhysicalMaterial
          color="#e0f7ff"
          metalness={0.2}
          roughness={0.1}
          transmission={0.7}
          thickness={0.8}
          envMapIntensity={1.5}
          clearcoat={1}
          clearcoatRoughness={0.05}
          transparent
          opacity={0.9}
          emissive="#0ea5e9"
          emissiveIntensity={0.3}
        />
      </RoundedBox>

      {/* Inner glowing core */}
      <mesh ref={innerGlowRef}>
        <boxGeometry args={[1.2, 1.2, 1.2]} />
        <meshBasicMaterial
          color="#0ea5e9"
          transparent
          opacity={0.4}
        />
      </mesh>

      {/* Solid inner cube for structure */}
      <mesh>
        <boxGeometry args={[0.8, 0.8, 0.8]} />
        <meshStandardMaterial
          color="#0ea5e9"
          emissive="#06b6d4"
          emissiveIntensity={1.5}
          metalness={0.8}
          roughness={0.2}
        />
      </mesh>

      {/* FS Logo - Front - Larger and brighter */}
      <Text
        position={[0, 0, 0.95]}
        fontSize={1}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.05}
        outlineColor="#0ea5e9"
      >
        FS
      </Text>

      {/* FS Logo - Back */}
      <Text
        position={[0, 0, -0.95]}
        rotation={[0, Math.PI, 0]}
        fontSize={1}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.05}
        outlineColor="#0ea5e9"
      >
        FS
      </Text>

      {/* Strong point lights */}
      <pointLight position={[0, 0, 0]} intensity={5} color="#0ea5e9" distance={8} />
      <pointLight position={[3, 3, 3]} intensity={2} color="#06b6d4" distance={6} />
      <pointLight position={[-3, -3, -3]} intensity={2} color="#0ea5e9" distance={6} />
      <pointLight position={[0, 4, 0]} intensity={3} color="#06b6d4" distance={7} />
    </group>
  )
}
