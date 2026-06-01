import { Github, Twitter, Linkedin } from 'lucide-react'

export default function FintechFooter() {
  const footerLinks = {
    product: [
      { label: 'Platform', href: '#product' },
      { label: 'Intelligence Modules', href: '#intelligence' },
      { label: 'Explainability', href: '#explainability' },
      { label: 'Security', href: '#security' },
    ],
    company: [
      { label: 'About', href: '#' },
      { label: 'Contact', href: '#' },
      { label: 'Privacy', href: '#' },
      { label: 'Terms', href: '#' },
    ],
  }

  const socialLinks = [
    { icon: Twitter, href: '#', label: 'Twitter' },
    { icon: Linkedin, href: '#', label: 'LinkedIn' },
    { icon: Github, href: '#', label: 'GitHub' },
  ]

  return (
    <footer className="relative overflow-hidden bg-[radial-gradient(circle_at_88%_12%,rgba(32,169,154,0.18),transparent_32%),linear-gradient(145deg,#08111f_0%,#0d1726_55%,#132337_100%)] text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        {/* Main footer content */}
        <div className="grid md:grid-cols-4 gap-8 mb-12">
          {/* Brand */}
          <div className="md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-[linear-gradient(145deg,#0d1726,#1c324b)] ring-1 ring-white/12 rounded-xl flex items-center justify-center shadow-navy-card">
                <span className="text-white font-bold text-sm">FS</span>
              </div>
              <span className="text-white font-semibold text-lg">
                FinSight CFO
              </span>
            </div>
            <p className="text-white/70 text-sm leading-relaxed max-w-md">
              AI financial intelligence platform for SME cashflow, credit readiness,
              and funding decisions.
            </p>
          </div>

          {/* Product links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Product</h3>
            <ul className="space-y-2">
              {footerLinks.product.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-white/70 hover:text-white transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Company links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Company</h3>
            <ul className="space-y-2">
              {footerLinks.company.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-white/70 hover:text-white transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="py-8 border-t border-white/10">
          <div className="bg-softform-amber-200/10 border border-softform-amber-200/20 rounded-2xl p-4 mb-8 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
            <p className="text-sm text-white/90 leading-relaxed">
              <strong className="text-white">Important Disclaimer:</strong> FinSight CFO
              provides indicative financial intelligence only. It is not audited financial
              advice, lending approval, or investment advice.
            </p>
          </div>

          {/* Bottom bar */}
          <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
            <p className="text-white/60 text-sm">
              © 2026 FinSight CFO. All rights reserved.
            </p>

            {/* Social links */}
            <div className="flex items-center space-x-4">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  aria-label={social.label}
                  className="w-10 h-10 bg-white/8 rounded-2xl flex items-center justify-center hover:bg-white/14 transition-colors shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]"
                >
                  <social.icon className="w-5 h-5 text-white/70" />
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
