import { useEffect, useState, useCallback, useRef } from 'react'
import { checkHealth } from '../lib/api'

export default function ConnectionStatus() {
  const [state, setState] = useState('checking')
  const [detail, setDetail] = useState('')
  const [fix, setFix] = useState('')
  const attemptsRef = useRef(0)

  const runCheck = useCallback(async (isRetryable) => {
    try {
      const res = await checkHealth()
      attemptsRef.current = 0
      setFix(res.fix || '')
      if (res.groq === 'ok' && res.model_available !== false) { setState('ok'); setDetail(`model: ${res.model}`) }
      else { setState('warn'); setDetail(res.groq) }
    } catch (err) {
      attemptsRef.current += 1
      if (isRetryable && attemptsRef.current < 3) { setTimeout(() => runCheck(true), 1200) }
      else { setState('down'); setDetail(err.message) }
    }
  }, [])

  useEffect(() => {
    runCheck(true)
    const interval = setInterval(() => runCheck(false), 20000)
    return () => clearInterval(interval)
  }, [runCheck])

  const config = {
    checking: { color: 'bg-base-muted', label: 'Checking backend…', pulse: true },
    ok: { color: 'bg-signal-teal', label: 'Backend connected', pulse: false },
    warn: { color: 'bg-signal-amber', label: 'Backend up, Groq needs attention', pulse: true },
    down: { color: 'bg-signal-red', label: 'Backend unreachable', pulse: true },
  }[state]

  return (
    <button onClick={() => { setState('checking'); attemptsRef.current = 0; runCheck(true) }} className="group relative flex items-center gap-2 cursor-pointer" title="Click to recheck">
      <span className={`w-1.5 h-1.5 rounded-full ${config.color} ${config.pulse ? 'pulse-dot' : ''}`} />
      <span className="text-[11px] font-mono text-base-muted">{config.label}</span>
      {detail && (
        <div className="absolute top-full right-0 mt-2 w-72 rounded-md border border-base-border bg-base-panel2 p-3 text-[11px] text-base-muted leading-relaxed opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-10 shadow-xl text-left">
          <p>{detail}</p>
          {fix && <p className="mt-1 text-signal-amber font-semibold">{fix}</p>}
        </div>
      )}
    </button>
  )
}
