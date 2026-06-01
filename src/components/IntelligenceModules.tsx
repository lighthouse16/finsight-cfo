import React from 'react';
import { motion } from 'framer-motion';
import { SignalIcon3D } from './visual/SignalIcon3D';
import { SourceTrailVisual } from './visual/SourceTrailVisual';
import { IntelligenceCoreVisual } from './visual/IntelligenceCoreVisual';
import { useReducedMotion } from '../hooks/useReducedMotion';

interface Module {
  id: string;
  title: string;
  audience: string;
  question: string;
  visualType: 'core' | 'trail' | 'flow' | 'network' | 'radar';
  signalType: 'positive' | 'neutral' | 'caution' | 'active';
}

const modules: Module[] = [
  {
    id: 'cashflow',
    title: 'Cashflow Cockpit',
    audience: 'For CFOs and Finance Teams',
    question: 'When will we run out of cash?',
    visualType: 'flow',
    signalType: 'active',
  },
  {
    id: 'credit',
    title: 'Credit Readiness',
    audience: 'For Business Owners',
    question: 'Are we ready to apply for financing?',
    visualType: 'trail',
    signalType: 'positive',
  },
  {
    id: 'advisor',
    title: 'Advisor Recommendations',
    audience: 'For Relationship Managers',
    question: 'What should we recommend to this client?',
    visualType: 'network',
    signalType: 'neutral',
  },
  {
    id: 'ai-cfo',
    title: 'AI CFO Assistant',
    audience: 'For All Stakeholders',
    question: 'What does our financial data tell us?',
    visualType: 'core',
    signalType: 'active',
  },
  {
    id: 'funding',
    title: 'Funding Report',
    audience: 'For Founders and CEOs',
    question: 'What financing options are available?',
    visualType: 'radar',
    signalType: 'positive',
  },
];

interface ModuleCardProps {
  module: Module;
  index: number;
}

const ModuleCard: React.FC<ModuleCardProps> = ({ module, index }) => {
  const prefersReducedMotion = useReducedMotion();

  const renderVisual = () => {
    switch (module.visualType) {
      case 'core':
        return (
          <div className="absolute inset-0 flex items-center justify-center opacity-20 group-hover:opacity-30 transition-opacity duration-500">
            <IntelligenceCoreVisual
              size="sm"
              variant="compact"
              showParticles={false}
              showOrbits={true}
            />
          </div>
        );
      case 'trail':
        return (
          <div className="absolute inset-0 flex items-center justify-center opacity-20 group-hover:opacity-30 transition-opacity duration-500">
            <SourceTrailVisual
              variant="horizontal"
              showLabels={false}
              animated={!prefersReducedMotion}
            />
          </div>
        );
      case 'flow':
        return (
          <div className="absolute inset-0 overflow-hidden">
            <svg
              className="w-full h-full opacity-10 group-hover:opacity-20 transition-opacity duration-500"
              viewBox="0 0 200 200"
              fill="none"
            >
              <motion.path
                d="M20,100 Q60,60 100,100 T180,100"
                stroke="var(--color-signal-cyan)"
                strokeWidth="2"
                strokeLinecap="round"
                fill="none"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              />
              <motion.path
                d="M20,120 Q60,160 100,120 T180,120"
                stroke="var(--color-signal-teal)"
                strokeWidth="2"
                strokeLinecap="round"
                fill="none"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{
                  duration: 2,
                  delay: 0.5,
                  repeat: Infinity,
                  ease: 'linear',
                }}
              />
            </svg>
          </div>
        );
      case 'network':
        return (
          <div className="absolute inset-0 overflow-hidden">
            <svg
              className="w-full h-full opacity-10 group-hover:opacity-20 transition-opacity duration-500"
              viewBox="0 0 200 200"
              fill="none"
            >
              <circle cx="100" cy="100" r="4" fill="var(--color-signal-cyan)" />
              <circle cx="60" cy="60" r="3" fill="var(--color-signal-teal)" />
              <circle cx="140" cy="60" r="3" fill="var(--color-signal-teal)" />
              <circle cx="60" cy="140" r="3" fill="var(--color-signal-teal)" />
              <circle cx="140" cy="140" r="3" fill="var(--color-signal-teal)" />
              <line
                x1="100"
                y1="100"
                x2="60"
                y2="60"
                stroke="var(--color-signal-cyan)"
                strokeWidth="1"
                opacity="0.5"
              />
              <line
                x1="100"
                y1="100"
                x2="140"
                y2="60"
                stroke="var(--color-signal-cyan)"
                strokeWidth="1"
                opacity="0.5"
              />
              <line
                x1="100"
                y1="100"
                x2="60"
                y2="140"
                stroke="var(--color-signal-cyan)"
                strokeWidth="1"
                opacity="0.5"
              />
              <line
                x1="100"
                y1="100"
                x2="140"
                y2="140"
                stroke="var(--color-signal-cyan)"
                strokeWidth="1"
                opacity="0.5"
              />
            </svg>
          </div>
        );
      case 'radar':
        return (
          <div className="absolute inset-0 overflow-hidden">
            <svg
              className="w-full h-full opacity-10 group-hover:opacity-20 transition-opacity duration-500"
              viewBox="0 0 200 200"
              fill="none"
            >
              <circle
                cx="100"
                cy="100"
                r="30"
                stroke="var(--color-signal-cyan)"
                strokeWidth="1"
                opacity="0.3"
              />
              <circle
                cx="100"
                cy="100"
                r="50"
                stroke="var(--color-signal-cyan)"
                strokeWidth="1"
                opacity="0.2"
              />
              <circle
                cx="100"
                cy="100"
                r="70"
                stroke="var(--color-signal-cyan)"
                strokeWidth="1"
                opacity="0.1"
              />
              <motion.line
                x1="100"
                y1="100"
                x2="100"
                y2="30"
                stroke="var(--color-signal-emerald)"
                strokeWidth="2"
                initial={{ rotate: 0 }}
                animate={{ rotate: 360 }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: 'linear',
                }}
                style={{ transformOrigin: '100px 100px' }}
              />
            </svg>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-100px' }}
      transition={{
        duration: 0.6,
        delay: index * 0.1,
        ease: [0.33, 1, 0.68, 1],
      }}
      className="group relative"
    >
      <motion.div
        className="relative h-full bg-white/80 backdrop-blur-sm rounded-xl border border-slate-200/60 overflow-hidden shadow-institutional hover:shadow-elevated transition-all duration-500"
        whileHover={
          prefersReducedMotion
            ? {}
            : {
                y: -4,
                transition: { duration: 0.3 },
              }
        }
      >
        {/* Background visual */}
        {renderVisual()}

        {/* Content */}
        <div className="relative z-10 p-8">
          {/* Signal indicator */}
          <div className="flex items-start justify-between mb-6">
            <SignalIcon3D
              type={module.signalType}
              size="sm"
              animated={!prefersReducedMotion}
              intensity="subtle"
            />
            <div className="w-2 h-2 rounded-full bg-gradient-to-br from-cyan-400 to-teal-500 opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
          </div>

          {/* Title */}
          <h3 className="text-2xl font-semibold text-slate-900 mb-3 group-hover:text-cyan-700 transition-colors duration-300">
            {module.title}
          </h3>

          {/* Audience */}
          <p className="text-sm font-medium text-slate-500 mb-4 uppercase tracking-wide">
            {module.audience}
          </p>

          {/* Question */}
          <p className="text-base text-slate-700 leading-relaxed">
            {module.question}
          </p>

          {/* Hover glow effect */}
          <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none glow-signal" />
        </div>

        {/* Bottom accent line */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-teal-500 to-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      </motion.div>
    </motion.div>
  );
};

export const IntelligenceModules: React.FC = () => {
  return (
    <section className="py-24 px-6 bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-7xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 mb-6"
          >
            <SignalIcon3D type="active" size="sm" animated={true} />
            <span className="text-sm font-semibold text-slate-600 uppercase tracking-wide">
              Intelligence Modules
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl md:text-5xl font-bold text-slate-900 mb-6"
          >
            Purpose-Built Financial Intelligence
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg text-slate-600 max-w-3xl mx-auto"
          >
            Each module combines your financial records with market intelligence
            to deliver review-ready insights for specific stakeholder needs.
          </motion.p>
        </div>

        {/* Module grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {modules.map((module, index) => (
            <ModuleCard key={module.id} module={module} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
};
