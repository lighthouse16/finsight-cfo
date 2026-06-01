import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import FloatingCard from './FloatingCard'
import {
  CashflowSignalCard,
  CreditReadinessCard,
  ReceivablesPressureCard,
  AdvisorActionCard,
  SourceTrailCard,
  KeyAssumptionsCard,
  FundingReadinessCard,
  FinancialRecordsSidebar,
} from './MetricCards'

export default function Hero3DScene() {
  return (
    <div className="relative w-full h-[600px] lg:h-[700px] border-4 border-red-500">
      <div className="absolute top-0 left-0 bg-yellow-300 text-black p-4 z-50">
        TEST - Hero3DScene is rendering!
      </div>
      {/* 3D Canvas with dark background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-900 to-cyan-900">
        <Canvas>
          <PerspectiveCamera makeDefault position={[0, 0, 5]} fov={50} />
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1} />
          
          {/* Simple test cube */}
          <mesh>
            <boxGeometry args={[2, 2, 2]} />
            <meshStandardMaterial color="#0ea5e9" emissive="#0ea5e9" emissiveIntensity={0.5} />
          </mesh>
          
          <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={1} />
        </Canvas>
      </div>

      {/* Floating UI Cards */}
      <FloatingCard delay={0.3} className="w-64 p-0" position={{ top: '5%', left: '3%' }}>
        <CashflowSignalCard />
      </FloatingCard>

      <FloatingCard delay={0.4} className="w-72 p-0" position={{ top: '3%', right: '20%' }}>
        <CreditReadinessCard />
      </FloatingCard>

      <FloatingCard delay={0.5} className="w-56 p-0" position={{ top: '8%', right: '3%' }}>
        <ReceivablesPressureCard />
      </FloatingCard>

      <FloatingCard delay={0.6} className="w-64 p-0" position={{ bottom: '20%', right: '5%' }}>
        <AdvisorActionCard />
      </FloatingCard>

      <FloatingCard delay={0.7} className="w-48 p-0" position={{ bottom: '30%', left: '5%' }}>
        <SourceTrailCard />
      </FloatingCard>

      <FloatingCard delay={0.8} className="w-52 p-0" position={{ bottom: '12%', left: '22%' }}>
        <KeyAssumptionsCard />
      </FloatingCard>

      <FloatingCard delay={0.9} className="w-60 p-0" position={{ bottom: '5%', right: '28%' }}>
        <FundingReadinessCard />
      </FloatingCard>

      <FloatingCard delay={0.5} className="w-56 p-0" position={{ top: '25%', left: '1%' }}>
        <FinancialRecordsSidebar />
      </FloatingCard>
    </div>
  )
}
