import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

interface WorkflowFooterProps {
  title: string
  description: string
  linkTo: string
  linkLabel: string
}

export default function WorkflowFooter({
  title,
  description,
  linkTo,
  linkLabel,
}: WorkflowFooterProps) {
  return (
    <section className="flex flex-col sm:flex-row gap-6 items-center justify-between p-8 rounded-[36px] border border-white/70 bg-gradient-to-r from-softform-mist-100/50 to-white/50 backdrop-blur-md shadow-base-card">
      <div className="space-y-1.5 text-center sm:text-left max-w-2xl">
        <p className="font-semibold text-softform-navy-950 text-base">{title}</p>
        <p className="text-xs leading-relaxed text-softform-text-secondary">
          {description}
        </p>
      </div>
      <Link
        to={linkTo}
        className="inline-flex items-center justify-center gap-1.5 rounded-xl bg-softform-navy-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-softform-navy-800 transition shadow-sm shrink-0"
      >
        {linkLabel}
        <ArrowRight size={14} />
      </Link>
    </section>
  )
}
