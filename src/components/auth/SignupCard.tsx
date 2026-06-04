import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

export default function SignupCard() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [company, setCompany] = useState('')
  const [password, setPassword] = useState('')
  const [acceptedNote, setAcceptedNote] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<{
    email?: string
    company?: string
    password?: string
    acceptedNote?: string
  }>({})

  const validate = () => {
    const newErrors: typeof errors = {}

    if (!email) {
      newErrors.email = 'Email is required.'
    } else if (!/^\S+@\S+\.\S+$/.test(email)) {
      newErrors.email = 'Enter a valid email.'
    }
    if (!company.trim()) {
      newErrors.company = 'Company name is required.'
    }
    if (!password) {
      newErrors.password = 'Password is required.'
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters.'
    }
    if (!acceptedNote) {
      newErrors.acceptedNote = 'Please acknowledge the note.'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!validate()) return

    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      navigate('/platform/overview')
    }, 650)
  }

  return (
    <article className="softform-panel w-full max-w-[500px] rounded-[30px] p-5 shadow-floating-panel sm:p-6">
      <div className="mb-5 text-center">
        <div className="mx-auto inline-flex items-center rounded-full bg-white/68 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-softform-teal-deep ring-1 ring-white/80">
          Account setup
        </div>
        <h1 className="mt-3 text-2xl font-bold tracking-[-0.035em] text-softform-navy-950 sm:text-3xl">Create account</h1>
        <p className="mt-2 text-sm leading-5 text-softform-text-secondary">Start using FinSight CFO.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3.5" noValidate>
        <div>
          <label htmlFor="signup-company" className="block text-sm font-bold text-softform-navy-900">
            Company name
          </label>
          <input
            id="signup-company"
            name="company"
            type="text"
            autoComplete="organization"
            value={company}
            onChange={(event) => {
              setCompany(event.target.value)
              if (errors.company) setErrors({ ...errors, company: undefined })
            }}
            className={`mt-1.5 block w-full rounded-2xl border-0 bg-white/74 px-4 py-3 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset transition-all focus:ring-2 focus:ring-inset sm:text-sm ${
              errors.company ? 'ring-red-300 focus:ring-red-500' : 'ring-softform-navy-950/10 focus:ring-softform-teal-500'
            }`}
            aria-invalid={errors.company ? 'true' : 'false'}
            aria-describedby={errors.company ? 'signup-company-error' : undefined}
          />
          {errors.company && <p className="mt-1 text-xs font-semibold text-red-600" id="signup-company-error">{errors.company}</p>}
        </div>

        <div>
          <label htmlFor="signup-email" className="block text-sm font-bold text-softform-navy-900">
            Email
          </label>
          <input
            id="signup-email"
            name="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value)
              if (errors.email) setErrors({ ...errors, email: undefined })
            }}
            className={`mt-1.5 block w-full rounded-2xl border-0 bg-white/74 px-4 py-3 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset transition-all focus:ring-2 focus:ring-inset sm:text-sm ${
              errors.email ? 'ring-red-300 focus:ring-red-500' : 'ring-softform-navy-950/10 focus:ring-softform-teal-500'
            }`}
            aria-invalid={errors.email ? 'true' : 'false'}
            aria-describedby={errors.email ? 'signup-email-error' : undefined}
          />
          {errors.email && <p className="mt-1 text-xs font-semibold text-red-600" id="signup-email-error">{errors.email}</p>}
        </div>

        <div>
          <label htmlFor="signup-password" className="block text-sm font-bold text-softform-navy-900">
            Password
          </label>
          <div className="relative mt-1.5">
            <input
              id="signup-password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="new-password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value)
                if (errors.password) setErrors({ ...errors, password: undefined })
              }}
              className={`block w-full rounded-2xl border-0 bg-white/74 py-3 pl-4 pr-11 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset transition-all focus:ring-2 focus:ring-inset sm:text-sm ${
                errors.password ? 'ring-red-300 focus:ring-red-500' : 'ring-softform-navy-950/10 focus:ring-softform-teal-500'
              }`}
              aria-invalid={errors.password ? 'true' : 'false'}
              aria-describedby={errors.password ? 'signup-password-error' : 'signup-password-help'}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-softform-text-muted transition hover:text-softform-text-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-softform-teal-500"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="h-5 w-5" aria-hidden="true" /> : <Eye className="h-5 w-5" aria-hidden="true" />}
            </button>
          </div>
          {errors.password ? (
            <p className="mt-1 text-xs font-semibold text-red-600" id="signup-password-error">{errors.password}</p>
          ) : (
            <p className="mt-1 text-xs text-softform-text-muted" id="signup-password-help">Minimum 8 characters.</p>
          )}
        </div>

        <div>
          <label className="flex items-start gap-3 rounded-2xl bg-white/46 px-3 py-2.5 text-sm font-semibold leading-5 text-softform-text-secondary ring-1 ring-white/70">
            <input
              id="indicative-note"
              name="indicative-note"
              type="checkbox"
              checked={acceptedNote}
              onChange={(event) => {
                setAcceptedNote(event.target.checked)
                if (errors.acceptedNote) setErrors({ ...errors, acceptedNote: undefined })
              }}
              className="mt-0.5 h-4 w-4 rounded border-softform-navy-950/20 text-softform-teal-600 focus:ring-softform-teal-500"
              aria-invalid={errors.acceptedNote ? 'true' : 'false'}
              aria-describedby={errors.acceptedNote ? 'indicative-note-error' : undefined}
            />
            <span>I understand financial intelligence is indicative only.</span>
          </label>
          {errors.acceptedNote && <p className="mt-1 text-xs font-semibold text-red-600" id="indicative-note-error">{errors.acceptedNote}</p>}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] px-4 py-3.5 text-sm font-bold text-white shadow-[0_18px_42px_rgba(8,17,31,0.22)] transition-all hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-softform-teal-500 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              Creating account...
            </>
          ) : (
            'Create account'
          )}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-softform-text-secondary">
        Already have an account?{' '}
        <Link to="/login" className="font-bold text-softform-teal-deep transition hover:text-softform-navy-900">
          Sign in
        </Link>
      </p>
    </article>
  )
}
