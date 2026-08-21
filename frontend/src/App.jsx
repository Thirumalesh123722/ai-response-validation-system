import { useState, useEffect, useCallback } from 'react'
import EvaluationForm from './components/EvaluationForm'
import ScoreCard from './components/ScoreCard'
import VerdictBanner from './components/VerdictBanner'
import DimensionRadar from './components/DimensionRadar'
import PipelineLoader from './components/PipelineLoader'
import ConnectionStatus from './components/ConnectionStatus'
import BatchEvaluation from './components/BatchEvaluation'
import SubmissionSummary from './components/SubmissionSummary'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import Signup from './components/Signup'
import { evaluateResponse } from './lib/api'
import { authFetch } from './lib/auth'
import { getAccessToken, logout as authLogout } from './lib/auth'

function MainApp({ currentUser, onLogout }) {
  const [mode, setMode] = useState('single')
  const [result, setResult] = useState(null)
  const [submission, setSubmission] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (payload) => {
    setIsLoading(true)
    setError(null)
    setResult(null)
    setSubmission({ question: payload.question, aiResponse: payload.ai_response })
    try {
      const res = await evaluateResponse(payload)
      setResult(res)
    } catch (err) {
      setError(err.message || 'Evaluation failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-base-border sticky top-0 z-20 backdrop-blur-md bg-base-bg/80">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-signal-teal/10 border border-signal-teal/30 flex items-center justify-center">
              <span className="font-display font-bold text-signal-teal text-base">V</span>
            </div>
            <div>
              <h1 className="font-display font-semibold text-base leading-none tracking-tight">Veritas</h1>
              <p className="text-[11px] text-base-muted font-mono leading-none mt-1">{currentUser.organization_name}</p>
            </div>
          </div>
          <div className="flex items-center gap-5">
            <ConnectionStatus />
            <div className="text-right hidden sm:block">
              <p className="text-xs text-base-text leading-none">{currentUser.full_name}</p>
              <p className="text-[10px] text-base-muted leading-none mt-1">{currentUser.email}</p>
            </div>
            <button onClick={onLogout} className="text-xs font-mono text-base-muted hover:text-signal-red transition-colors">Log out</button>
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-6 flex gap-1 -mb-px">
          {[['single', 'Single Evaluation'], ['batch', 'Batch Evaluation'], ['dashboard', 'Dashboard']].map(([key, label]) => (
            <button key={key} onClick={() => setMode(key)}
              className={`px-4 py-2 text-xs font-mono uppercase tracking-widest border-b-2 transition-colors ${mode === key ? 'border-signal-teal text-base-text' : 'border-transparent text-base-muted hover:text-base-text'}`}>
              {label}
            </button>
          ))}
        </div>
      </header>

      {mode === 'batch' ? (
        <main className="max-w-6xl mx-auto px-6 py-10"><BatchEvaluation /></main>
      ) : mode === 'dashboard' ? (
        <main className="max-w-6xl mx-auto px-6 py-10"><Dashboard /></main>
      ) : (
        <main className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-8">
          <section>
            <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase mb-3">01 — Input</p>
            <EvaluationForm onSubmit={handleSubmit} isLoading={isLoading} />
          </section>

          <section className="flex flex-col gap-6">
            <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase">02 — Evaluation</p>

            {isLoading && <PipelineLoader />}

            {error && (
              <div className="rounded-lg border border-signal-red/40 bg-signal-red/5 p-5">
                <p className="font-mono text-[11px] tracking-widest text-signal-red uppercase mb-1">Evaluation Error</p>
                <p className="text-sm text-base-text">{error}</p>
              </div>
            )}

            {!isLoading && !error && !result && (
              <div className="rounded-lg border border-dashed border-base-border p-10 text-center">
                <p className="text-sm text-base-muted">Submit a question and AI response to see per-dimension scores, a groundedness check, and a final verdict here.</p>
              </div>
            )}

            {result && (
              <>
                {submission && (<div className="animate-rise"><SubmissionSummary question={submission.question} aiResponse={submission.aiResponse} /></div>)}
                <div className="animate-rise" style={{ animationDelay: '40ms' }}>
                  <VerdictBanner finalScore={result.final_score} verdictLabel={result.verdict_label} verdict={result.verdict} />
                </div>
                <div className="animate-rise" style={{ animationDelay: '80ms' }}>
                  <DimensionRadar relevance={result.relevance_score} accuracy={result.accuracy_score} hallucination={result.hallucination_score} completeness={result.completeness_score} />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div className="animate-rise" style={{ animationDelay: '140ms' }}><ScoreCard eyebrow="Dimension 01" label="Relevance" score={result.relevance_score} reasoning={result.relevance_reasoning} accent="blue" /></div>
                  <div className="animate-rise" style={{ animationDelay: '190ms' }}><ScoreCard eyebrow="Dimension 02" label="Accuracy" score={result.accuracy_score} reasoning={result.accuracy_reasoning} accent="violet" /></div>
                  <div className="animate-rise" style={{ animationDelay: '240ms' }}><ScoreCard eyebrow="Dimension 03" label="Groundedness" score={result.hallucination_score} reasoning={result.hallucination_reasoning} flags={result.hallucination_flags} accent="red" /></div>
                  <div className="animate-rise" style={{ animationDelay: '290ms' }}><ScoreCard eyebrow="Dimension 04" label="Completeness" score={result.completeness_score} reasoning={result.completeness_reasoning} accent="teal" /></div>
                </div>
                {result.retrieved_context && result.retrieved_context.length > 0 && (
                  <div className="rounded-lg border border-base-border card-surface p-5 animate-rise" style={{ animationDelay: '340ms' }}>
                    <p className="font-mono text-[11px] tracking-widest text-base-muted uppercase mb-3">Retrieved Reference Context</p>
                    <div className="space-y-2 max-h-60 overflow-y-auto scrollbar-thin pr-2">
                      {result.retrieved_context.map((chunk, i) => (<p key={i} className="text-xs text-base-muted leading-relaxed border-l-2 border-base-border pl-3">{chunk}</p>))}
                    </div>
                  </div>
                )}
              </>
            )}
          </section>
        </main>
      )}
    </div>
  )
}

export default function App() {
  const [authView, setAuthView] = useState('login') // 'login' | 'signup'
  const [currentUser, setCurrentUser] = useState(null)
  const [checkingAuth, setCheckingAuth] = useState(true)

  const loadCurrentUser = useCallback(async () => {
    if (!getAccessToken()) {
      setCurrentUser(null)
      setCheckingAuth(false)
      return
    }
    try {
      const res = await authFetch('/auth/me')
      if (!res.ok) throw new Error('not authenticated')
      const data = await res.json()
      setCurrentUser(data)
    } catch {
      setCurrentUser(null)
    } finally {
      setCheckingAuth(false)
    }
  }, [])

  useEffect(() => { loadCurrentUser() }, [loadCurrentUser])

  const handleLogout = async () => {
    await authLogout()
    setCurrentUser(null)
  }

  if (checkingAuth) {
    return <div className="min-h-screen flex items-center justify-center"><p className="text-sm text-base-muted">Loading…</p></div>
  }

  if (!currentUser) {
    return authView === 'login'
      ? <Login onSuccess={loadCurrentUser} onSwitchToSignup={() => setAuthView('signup')} />
      : <Signup onSuccess={loadCurrentUser} onSwitchToLogin={() => setAuthView('login')} />
  }

  return <MainApp currentUser={currentUser} onLogout={handleLogout} />
}
