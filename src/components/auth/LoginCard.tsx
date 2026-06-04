import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

export default function LoginCard() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showRecoveryMessage, setShowRecoveryMessage] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({})

  const validate = () => {
    const newErrors: { email?: string; password?: string } = {}

    if (!email) {
      newErrors.email = 'Work email is required.'
    } else if (!/^\S+@\S+\.\S+$/.test(email)) {
      newErrors.email = 'Enter a valid work email.'
    }

    if (!password) {
      newErrors.password = 'Password is required.'
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters.'
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
    <article className="softform-panel w-full max-w-[430px] rounded-[30px] p-5 shadow-floating-panel sm:p-6">
      <div className="mb-5 text-center">
        <div className="mx-auto inline-flex items-center rounded-full bg-white/68 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.16em] text-softform-teal-deep ring-1 ring-white/80">
          Secure access
        </div>
        <h1 className="mt-3 text-2xl font-bold tracking-[-0.035em] text-softform-navy-950 sm:text-3xl">Sign in</h1>
        <p className="mt-2 text-sm leading-5 text-softform-text-secondary">Access your FinSight CFO workspace.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="login-email" className="block text-sm font-bold text-softform-navy-900">
            Email
          </label>
          <input
            id="login-email"
            name="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value)
              if (errors.email) setErrors({ ...errors, email: undefined })
            }}
            className={`mt-2 block w-full rounded-2xl border-0 bg-white/74 px-4 py-3 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset transition-all focus:ring-2 focus:ring-inset sm:text-sm ${
              errors.email ? 'ring-red-300 focus:ring-red-500' : 'ring-softform-navy-950/10 focus:ring-softform-teal-500'
            }`}
            aria-invalid={errors.email ? 'true' : 'false'}
            aria-describedby={errors.email ? 'login-email-error' : undefined}
          />
          {errors.email && (
            <p className="mt-1.5 text-xs font-semibold text-red-600" id="login-email-error">
              {errors.email}
            </p>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between gap-4">
            <label htmlFor="login-password" className="block text-sm font-bold text-softform-navy-900">
              Password
            </label>
            <button
              type="button"
              onClick={() => setShowRecoveryMessage(true)}
              className="text-sm font-bold text-softform-teal-deep transition hover:text-softform-navy-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-softform-teal-500"
              aria-describedby={showRecoveryMessage ? 'password-recovery-note' : undefined}
            >
              Forgot your password?
            </button>
          </div>
          <div className="relative mt-2">
            <input
              id="login-password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value)
                if (errors.password) setErrors({ ...errors, password: undefined })
              }}
              className={`block w-full rounded-2xl border-0 bg-white/74 py-3 pl-4 pr-11 text-softform-navy-950 shadow-[inset_0_1px_3px_rgba(8,17,31,0.05)] ring-1 ring-inset transition-all focus:ring-2 focus:ring-inset sm:text-sm ${
                errors.password ? 'ring-red-300 focus:ring-red-500' : 'ring-softform-navy-950/10 focus:ring-softform-teal-500'
              }`}
              aria-invalid={errors.password ? 'true' : 'false'}
              aria-describedby={errors.password ? 'login-password-error' : showRecoveryMessage ? 'password-recovery-note' : undefined}
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
          {errors.password && (
            <p className="mt-1.5 text-xs font-semibold text-red-600" id="login-password-error">
              {errors.password}
            </p>
          )}
        </div>

        {showRecoveryMessage && (
          <p id="password-recovery-note" className="rounded-2xl bg-white/56 px-3 py-2 text-xs font-semibold leading-5 text-softform-text-secondary ring-1 ring-white/70">
            Password recovery will be available when live authentication is connected.
          </p>
        )}

        <label className="flex items-center gap-3 rounded-2xl bg-white/46 px-3 py-2.5 text-sm font-semibold text-softform-text-secondary ring-1 ring-white/70">
          <input id="remember-me" name="remember-me" type="checkbox" className="h-4 w-4 rounded border-softform-navy-950/20 text-softform-teal-600 focus:ring-softform-teal-500" />
          Keep me signed in
        </label>

        <button
          type="submit"
          disabled={isLoading}
          className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[linear-gradient(145deg,#0d1726,#1c324b)] px-4 py-3.5 text-sm font-bold text-white shadow-[0_18px_42px_rgba(8,17,31,0.22)] transition-all hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-softform-teal-500 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              Signing in...
            </>
          ) : (
            'Sign in'
          )}
        </button>
      </form>

      <p className="mt-5 text-center text-sm text-softform-text-secondary">
        New here?{' '}
        <Link to="/signup" className="font-bold text-softform-teal-deep transition hover:text-softform-navy-900">
          Create account
        </Link>
      </p>
    </article>
  )
}
