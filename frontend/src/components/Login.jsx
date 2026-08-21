import { useState } from 'react'
import { login } from '../lib/auth'

export default function Login({ onSuccess, onSwitchToSignup }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login({ email, password })
      onSuccess()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-9 h-9 rounded-md bg-signal-teal/10 border border-signal-teal/30 flex items-center justify-center">
            <span className="font-display font-bold text-signal-teal text-base">V</span>
          </div>
          <div>
            <h1 className="font-display font-semibold text-base leading-none">Veritas</h1>
            <p className="text-[11px] text-base-muted font-mono leading-none mt-1">AI Response Validation</p>
          </div>
        </div>

        <div className="rounded-lg border border-base-border card-surface p-6">
          <h2 className="font-display text-xl font-semibold mb-1">Log in</h2>
          <p className="text-sm text-base-muted mb-6">Welcome back.</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">Email</label>
              <input
                type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                className="mt-2 w-full rounded-md bg-base-panel2 border border-base-border px-3 py-2.5 text-sm text-base-text focus:outline-none focus:ring-1 focus:ring-signal-blue focus:border-signal-blue"
              />
            </div>
            <div>
              <label className="font-mono text-[11px] tracking-widest text-base-muted uppercase">Password</label>
              <input
                type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
                className="mt-2 w-full rounded-md bg-base-panel2 border border-base-border px-3 py-2.5 text-sm text-base-text focus:outline-none focus:ring-1 focus:ring-signal-blue focus:border-signal-blue"
              />
            </div>

            {error && (
              <div className="rounded-md border border-signal-red/40 bg-signal-red/5 p-3">
                <p className="text-xs text-signal-red">{error}</p>
              </div>
            )}

            <button
              type="submit" disabled={loading}
              className="mt-2 rounded-md bg-signal-blue disabled:opacity-50 text-base-bg font-display font-semibold text-sm py-2.5 hover:brightness-110 transition-all"
            >
              {loading ? 'Logging in…' : 'Log in'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-base-muted mt-5">
          Don't have an account?{' '}
          <button onClick={onSwitchToSignup} className="text-signal-teal hover:underline">Sign up</button>
        </p>
      </div>
    </div>
  )
}
