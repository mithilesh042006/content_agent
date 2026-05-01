import { useCallback, useEffect, useRef, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const TONES = ['professional', 'witty', 'authoritative', 'inspirational', 'casual']

/* ── Theme ─────────────────────────────────────────────────────────────
 * The pre-hydration script in index.html has already placed the correct
 * data-theme on <html>; this hook mirrors it into React state and exposes
 * a view-transition-aware toggle.
 * ────────────────────────────────────────────────────────────────────── */
function readInitialTheme() {
  if (typeof document === 'undefined') return 'light'
  const attr = document.documentElement.getAttribute('data-theme')
  return attr === 'dark' ? 'dark' : 'light'
}

function useTheme() {
  const [theme, setTheme] = useState(readInitialTheme)

  const setAttr = useCallback((next) => {
    document.documentElement.setAttribute('data-theme', next)
    try { localStorage.setItem('reachcraft-theme', next) } catch {}
    setTheme(next)
  }, [])

  const toggle = useCallback((event) => {
    const next = theme === 'dark' ? 'light' : 'dark'
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (reduced || !document.startViewTransition) {
      setAttr(next)
      return
    }

    const x = event?.clientX ?? window.innerWidth - 48
    const y = event?.clientY ?? 48
    const endRadius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y),
    )

    const transition = document.startViewTransition(() => setAttr(next))
    transition.ready
      .then(() => {
        document.documentElement.animate(
          {
            clipPath: [
              `circle(0 at ${x}px ${y}px)`,
              `circle(${endRadius}px at ${x}px ${y}px)`,
            ],
          },
          {
            duration: 620,
            easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
            pseudoElement: '::view-transition-new(root)',
          },
        )
      })
      .catch(() => {})
  }, [theme, setAttr])

  return { theme, toggle }
}

/* ── Brand mark ─────────────────────────────────────────────────────────
 * Two overlapping circles: a solid amber disc (the crafted point) and a
 * larger outlined ring (the reach).  Reused in the header, the hero, and
 * the favicon.  Outline inherits currentColor; fill is always amber.
 * ──────────────────────────────────────────────────────────────────────── */
function ReachCraftMark({ size = 22, strokeWidth = 1.6, ringOpacity = 0.5, className = '' }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      className={className}
      aria-hidden
    >
      <circle
        cx="13.5"
        cy="12"
        r="7.5"
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        opacity={ringOpacity}
      />
      <circle cx="9" cy="12" r="3.25" fill="var(--amber)" />
    </svg>
  )
}

/* ── Animated brand mark — hero ornament ────────────────────────────────
 * The ReachCraft logo with a single focused motion: the outer ring is the
 * reach (static), the amber disc is the craft point orbiting inside that
 * reach on a slow 5s loop. Disc radius + orbit radius are tuned so the
 * disc's outer edge tracks the ring's inner edge — it orbits the wall.
 * Respects prefers-reduced-motion.
 * ──────────────────────────────────────────────────────────────────────── */
function AnimatedBrandMark({ className = '' }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={`animated-brand-mark ${className}`}
      aria-hidden
    >
      {/* Static outer ring — the reach perimeter */}
      <circle
        cx="13.5" cy="12" r="7.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        opacity="0.72"
      />
      {/* Orbiting amber disc — loops inside the ring, tracking its inner wall */}
      <g className="brand-mark-orbit">
        <circle cx="9.7" cy="12" r="3.0" fill="var(--amber)" />
      </g>
    </svg>
  )
}

function Brand() {
  return (
    <a
      href="/"
      className="inline-flex items-center gap-2.5 text-ink hover:text-ink transition-colors"
    >
      <ReachCraftMark size={24} />
      <span
        className="font-display text-[17px] leading-none"
        style={{
          fontWeight: 500,
          fontVariationSettings: '"opsz" 18, "SOFT" 50',
          letterSpacing: '-0.005em',
        }}
      >
        ReachCraft
      </span>
    </a>
  )
}

/* ── Sun / Moon icons ───────────────────────────────────────────────── */
function SunIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      aria-hidden
    >
      <circle cx="12" cy="12" r="3.75" />
      <path d="M12 3v1.6 M12 19.4V21 M3 12h1.6 M19.4 12H21 M5.6 5.6l1.15 1.15 M17.25 17.25l1.15 1.15 M18.4 5.6l-1.15 1.15 M6.75 17.25l-1.15 1.15" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M20 14.8A8 8 0 1 1 9.2 4a6.5 6.5 0 0 0 10.8 10.8z" />
    </svg>
  )
}

function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === 'dark'
  return (
    <button
      type="button"
      onClick={onToggle}
      role="switch"
      aria-checked={isDark}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className="relative inline-flex items-center justify-center w-9 h-9 text-ink border border-ink/35 hover:border-ink hover:text-amber transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-amber focus-visible:ring-offset-2 focus-visible:ring-offset-paper overflow-hidden"
    >
      <span
        className="absolute inset-0 flex items-center justify-center"
        style={{
          opacity: isDark ? 0 : 1,
          transform: isDark ? 'rotate(90deg) scale(0.4)' : 'rotate(0) scale(1)',
          transition: 'opacity 340ms ease, transform 500ms cubic-bezier(0.5, 0.05, 0.2, 1)',
        }}
      >
        <SunIcon />
      </span>
      <span
        className="absolute inset-0 flex items-center justify-center"
        style={{
          opacity: isDark ? 1 : 0,
          transform: isDark ? 'rotate(0) scale(1)' : 'rotate(-90deg) scale(0.4)',
          transition: 'opacity 340ms ease, transform 500ms cubic-bezier(0.5, 0.05, 0.2, 1)',
        }}
      >
        <MoonIcon />
      </span>
    </button>
  )
}

const STAGES = [
  'Interpreting brief · mapping intent',
  'Selecting platform & optimal topic',
  'Simulating performance across channels',
  'Drafting platform-native copy',
  'Evaluating predicted vs actual outcome',
]

async function runPipeline(payload) {
  const res = await fetch(`${API_URL}/agent/pipeline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text?.slice(0, 200) || `Request failed (${res.status})`)
  }
  return res.json()
}

/* ─────────────────────────────────────────────────────────────────── */

function Header({ theme, onToggleTheme }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-ink/80 px-5 md:px-12 py-3.5">
      <Brand />
      <ThemeToggle theme={theme} onToggle={onToggleTheme} />
    </div>
  )
}

function Hero() {
  return (
    <section className="relative px-5 md:px-12 pt-14 md:pt-20 pb-10 md:pb-14 border-b border-ink/80">
      <div className="grid grid-cols-12 gap-6 items-center">
        <div className="col-span-12 md:col-span-8">
          <div className="flex items-center gap-4 md:gap-8 md:justify-between md:pr-2">
            <h1 className="display-xl text-[clamp(3.25rem,8vw,7rem)] text-ink">
              <span className="block">The craft</span>
              <span className="block">
                of <span className="display-italic text-amber">reach</span>
                <span className="text-amber">.</span>
              </span>
            </h1>
            <AnimatedBrandMark className="w-24 md:w-36 lg:w-44 h-auto flex-shrink-0 text-ink" />
          </div>
        </div>
        <div className="col-span-12 md:col-span-4 md:pl-8 md:border-l border-ink/30 pt-4 md:pt-0">
          <p className="font-display text-xl md:text-2xl lg:text-[1.65rem] leading-snug text-ink max-w-lg">
            A five-stage agentic analysis —
            <span className="italic"> interpret, decide, simulate, generate, learn</span>
            &nbsp;— delivered as a single report.
          </p>
        </div>
      </div>
    </section>
  )
}

/* ─────────────────────────────────────────────────────────────────── */

function Field({ label, value, onChange, placeholder, textarea, maxLength }) {
  const common =
    'w-full bg-transparent border-b border-ink/40 focus:border-amber outline-none py-2 text-ink placeholder:text-ink-muted/70 placeholder:italic transition-colors font-display text-lg'
  return (
    <label className="block">
      <div className="flex items-baseline justify-between mb-2">
        <span className="font-mono text-[10px] tracking-[0.3em] uppercase text-ink-muted">{label}</span>
        {maxLength && (
          <span className="font-mono text-[9px] text-ink-muted/70">
            {value.length}/{maxLength}
          </span>
        )}
      </div>
      {textarea ? (
        <textarea
          className={common + ' resize-none min-h-[70px] leading-snug'}
          rows={2}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          maxLength={maxLength}
        />
      ) : (
        <input
          className={common}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          maxLength={maxLength}
        />
      )}
    </label>
  )
}

function BriefForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    business_domain: '',
    content_goal: '',
    target_audience: '',
    tone: 'professional',
  })
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const canSubmit =
    form.business_domain.trim().length >= 2 &&
    form.content_goal.trim().length >= 5 &&
    form.target_audience.trim().length >= 3 &&
    !loading

  const fillSample = () =>
    setForm({
      business_domain: 'SaaS fintech for small businesses',
      content_goal: 'Increase signups for our new API product',
      target_audience: 'Startup founders and CTOs',
      tone: 'authoritative',
    })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (canSubmit) onSubmit(form)
      }}
      className="space-y-7"
    >
      <div className="flex items-baseline gap-4 pb-3 border-b border-ink">
        <span className="font-mono text-[10px] tracking-[0.3em] text-amber">00</span>
        <h2 className="font-display font-light text-3xl leading-none text-ink">Brief</h2>
        <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.25em] text-ink-muted">
          Intake
        </span>
      </div>

      <Field
        label="Business domain"
        value={form.business_domain}
        onChange={set('business_domain')}
        placeholder="e.g. SaaS fintech for small businesses"
        maxLength={200}
      />
      <Field
        label="Content goal"
        value={form.content_goal}
        onChange={set('content_goal')}
        placeholder="e.g. increase signups for our new API product"
        textarea
        maxLength={500}
      />
      <Field
        label="Target audience"
        value={form.target_audience}
        onChange={set('target_audience')}
        placeholder="e.g. startup founders and CTOs"
        maxLength={300}
      />

      <div>
        <div className="font-mono text-[10px] tracking-[0.3em] uppercase text-ink-muted mb-3">
          Tone of voice
        </div>
        <div className="flex flex-wrap gap-1.5">
          {TONES.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setForm((f) => ({ ...f, tone: t }))}
              className={`px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.18em] border transition-colors ${
                form.tone === t
                  ? 'bg-ink text-paper border-ink'
                  : 'border-ink/35 text-ink-soft hover:border-ink hover:text-ink'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-3 pt-2">
        <button
          type="submit"
          disabled={!canSubmit}
          className="group relative flex items-center justify-between gap-3 px-5 py-3 bg-ink text-paper font-mono text-[11px] tracking-[0.28em] uppercase border border-ink hover:bg-amber hover:border-amber disabled:opacity-35 disabled:hover:bg-ink disabled:cursor-not-allowed transition-colors"
        >
          <span>{loading ? 'Running…' : 'Run analysis'}</span>
          <span className="flex items-center gap-2">
            <span className="w-8 h-px bg-paper transition-all group-hover:w-16 group-disabled:w-8" />
            <span>→</span>
          </span>
        </button>

        <button
          type="button"
          onClick={fillSample}
          disabled={loading}
          className="self-start font-mono text-[10px] tracking-[0.2em] uppercase text-ink-muted hover:text-amber transition-colors disabled:opacity-40"
        >
          · Load sample brief
        </button>
      </div>
    </form>
  )
}

/* ─────────────────────────────────────────────────────────────────── */

function EmptyReport() {
  return (
    <div className="border border-ink/30 min-h-[520px] flex flex-col items-center justify-center gap-6 p-10 text-center fiber">
      <div className="w-14 h-14 border border-ink/40 flex items-center justify-center">
        <span className="font-display text-3xl text-ink-muted leading-none">—</span>
      </div>
      <div className="max-w-sm">
        <p className="font-mono text-[10px] tracking-[0.3em] uppercase text-ink-muted">
          Awaiting brief
        </p>
        <p className="font-display italic text-lg text-ink-soft mt-3 leading-snug">
          Submit a brief on the left. A five-stage strategy report will render here within ten seconds.
        </p>
      </div>
      <div className="grid grid-cols-5 gap-2 w-full max-w-lg font-mono text-[9px] uppercase tracking-[0.2em] text-ink-muted/80">
        <div className="border border-ink/20 py-2 text-center">00 · Interpret</div>
        <div className="border border-ink/20 py-2 text-center">01 · Decide</div>
        <div className="border border-ink/20 py-2 text-center">02 · Simulate</div>
        <div className="border border-ink/20 py-2 text-center">03 · Generate</div>
        <div className="border border-ink/20 py-2 text-center">04 · Learn</div>
      </div>
    </div>
  )
}

function LoadingReel() {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setTick((t) => Math.min(t + 1, STAGES.length - 1)), 1700)
    return () => clearInterval(id)
  }, [])
  return (
    <div className="border border-ink/30 p-6 md:p-10 min-h-[520px] fiber">
      <div className="flex items-center gap-3 font-mono text-[10px] tracking-[0.3em] uppercase text-amber">
        <span className="w-2 h-2 bg-amber blink" />
        Processing — live
      </div>
      <div className="mt-6 h-px bg-ink/20 relative overflow-hidden">
        <div className="absolute inset-y-0 left-0 w-full bg-amber draw-rule" />
      </div>
      <ul className="mt-10 space-y-3.5 font-mono text-sm">
        {STAGES.map((s, i) => (
          <li
            key={s}
            className={`flex items-center gap-4 transition-opacity duration-500 ${
              i <= tick ? 'opacity-100' : 'opacity-25'
            }`}
          >
            <span
              className={`w-5 text-center ${
                i < tick ? 'text-sage' : i === tick ? 'text-amber' : 'text-ink-muted'
              }`}
            >
              {i < tick ? '✓' : i === tick ? '▸' : '·'}
            </span>
            <span className={i === tick ? 'text-ink' : 'text-ink-soft'}>{s}</span>
            {i === tick && <span className="w-2 h-4 bg-ink blink" />}
          </li>
        ))}
      </ul>
      <p className="mt-12 pt-6 border-t border-ink/15 font-display italic text-ink-muted text-sm max-w-md">
        Average run — ten to fifteen seconds.
        Each stage calls the Groq inference engine, with deterministic fallbacks on failure.
      </p>
    </div>
  )
}

/* ─────────────────────────────────────────────────────────────────── */

function StageHeader({ num, title, meta }) {
  return (
    <div className="flex items-baseline justify-between pb-3 border-b border-ink">
      <div className="flex items-baseline gap-4">
        <span className="font-mono text-[10px] tracking-[0.3em] text-amber">{num}</span>
        <h3 className="font-display font-light text-2xl md:text-3xl text-ink leading-none">{title}</h3>
      </div>
      {meta && (
        <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-ink-muted">
          {meta}
        </span>
      )}
    </div>
  )
}

function DL({ label, children }) {
  return (
    <div>
      <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-1.5">
        {label}
      </div>
      <div className="font-display text-xl text-ink leading-snug">{children}</div>
    </div>
  )
}

/* ── Interpretation Card ─────────────────────────────────────────────── */

function InterpretationCard({ data }) {
  const pct = (n) => `${Math.round(n * 100)}%`
  return (
    <section className="rise border border-ink/30 p-6 md:p-8 fiber" style={{ animationDelay: '0ms' }}>
      <StageHeader num="00" title="Interpretation" meta="Brief parsed" />
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <DL label="Business type">
          <span className="text-amber">{data.business_type}</span>
        </DL>
        <DL label="Goal type">
          <span className="text-amber">{data.goal_type}</span>
        </DL>
        <DL label="Audience (refined)">
          <span className="text-sage">{data.audience_segment}</span>
        </DL>
      </div>
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        <DL label="Content objective">{data.inferred_content_objective}</DL>
        <DL label="Audience confidence">{pct(data.audience_inference_confidence)}</DL>
      </div>

      {data.candidate_angles?.length > 0 && (
        <div className="mt-6 pt-5 border-t border-ink/15">
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-3">
            Candidate content angles
          </div>
          <ul className="space-y-2">
            {data.candidate_angles.map((angle, i) => (
              <li key={i} className="flex gap-3 text-sm leading-relaxed text-ink-soft">
                <span className="font-mono text-amber text-xs mt-0.5">{i + 1}.</span>
                <span className="font-display">{angle}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.reasoning_trace && (
        <div className="mt-6 pt-5 border-t border-ink/15">
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            Reasoning trace
          </div>
          <p className="font-display italic text-sm leading-relaxed text-ink-soft max-w-3xl">
            &ldquo;{data.reasoning_trace}&rdquo;
          </p>
        </div>
      )}
    </section>
  )
}

/* ── Platform Scorecard (6 axes) ─────────────────────────────────────── */

function PlatformScorecard({ scores, winner }) {
  if (!scores?.length) return null
  const sorted = [...scores].sort((a, b) => b.weighted_total - a.weighted_total)
  const axes = [
    { key: 'audience_fit',   label: 'Aud.' },
    { key: 'goal_fit',       label: 'Goal' },
    { key: 'format_fit',     label: 'Fmt.' },
    { key: 'conversion_fit', label: 'Conv.' },
    { key: 'tone_fit',       label: 'Tone' },
    { key: 'timing_fit',     label: 'Time' },
  ]
  return (
    <div className="mt-8 pt-6 border-t border-ink/20">
      <div className="flex items-baseline justify-between mb-3">
        <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted">
          Platform scorecard · 6 candidates · 6 axes
        </div>
        <div className="font-mono text-[10px] tracking-[0.2em] uppercase text-ink-muted/70">
          Weighted total reflects strategic importance
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full font-mono text-[11px] border-collapse">
          <thead>
            <tr className="text-ink-muted text-[9px] uppercase tracking-[0.22em]">
              <th className="text-left font-normal py-2 pr-3 border-b border-ink/20">Platform</th>
              {axes.map(a => (
                <th key={a.key} className="text-right font-normal py-2 px-2 border-b border-ink/20">{a.label}</th>
              ))}
              <th className="text-right font-normal py-2 px-2 border-b border-ink/20">Sum</th>
              <th className="text-right font-normal py-2 pl-3 border-b border-ink/20">W.Total</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(row => {
              const isWinner = row.platform === winner
              return (
                <tr
                  key={row.platform}
                  className={`border-b border-ink/10 ${isWinner ? 'bg-amber/8' : ''}`}
                >
                  <td className={`py-2 pr-3 ${isWinner ? 'text-amber' : 'text-ink'}`}>
                    {isWinner && <span className="mr-1.5">▸</span>}
                    <span className={isWinner ? 'font-semibold' : ''}>{row.platform}</span>
                  </td>
                  {axes.map(a => (
                    <td key={a.key} className={`text-right py-2 px-2 ${isWinner ? 'text-ink' : 'text-ink-soft'}`}>
                      {row[a.key].toFixed(1)}
                    </td>
                  ))}
                  <td className={`text-right py-2 px-2 ${isWinner ? 'text-ink' : 'text-ink-soft'}`}>
                    {row.total.toFixed(1)}
                  </td>
                  <td className={`text-right py-2 pl-3 font-semibold ${isWinner ? 'text-amber' : 'text-ink'}`}>
                    {row.weighted_total.toFixed(2)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ── Decision Card ───────────────────────────────────────────────────── */

function DecisionCard({ data }) {
  return (
    <section className="rise border border-ink/30 p-6 md:p-8 fiber" style={{ animationDelay: '40ms' }}>
      <StageHeader num="01" title="Decision" meta="Strategy selected" />
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        <DL label="Topic">{data.topic}</DL>
        <DL label="Platform">
          <span className="text-amber">{data.platform}</span>
        </DL>
        <DL label="Optimal posting">{data.posting_time}</DL>
      </div>

      {/* Candidate topics */}
      {data.candidate_topics?.length > 0 && (
        <div className="mt-6 pt-5 border-t border-ink/15">
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-3">
            Candidate topics evaluated
          </div>
          <ul className="space-y-2">
            {data.candidate_topics.map((ct, i) => (
              <li key={i} className="flex gap-3 text-sm leading-relaxed">
                <span className={`font-mono text-xs mt-0.5 ${ct.selected ? 'text-amber' : 'text-ink-muted'}`}>
                  {ct.selected ? '▸' : '·'}
                </span>
                <div>
                  <span className={ct.selected ? 'text-ink font-medium' : 'text-ink-soft'}>{ct.angle}</span>
                  {ct.selected && (
                    <span className="ml-2 font-mono text-[9px] uppercase tracking-[0.2em] text-amber">
                      Selected
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.chosen_because && (
        <div className="mt-6 pt-5 border-t border-ink/15">
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            Chosen because
          </div>
          <p className="font-display text-lg leading-snug text-ink">{data.chosen_because}</p>
        </div>
      )}
      <div className="mt-6 pt-5 border-t border-ink/15">
        <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-3">
          Rationale
        </div>
        <p className="font-display italic text-lg leading-snug text-ink-soft max-w-3xl">
          &ldquo;{data.reason}&rdquo;
        </p>
      </div>
      <PlatformScorecard scores={data.platform_scores} winner={data.platform} />
    </section>
  )
}

/* ── Simulation Card ─────────────────────────────────────────────────── */

function MetricBlock({ label, value, unit, accent }) {
  const color =
    { amber: 'text-amber', blue: 'text-blue', sage: 'text-sage', ink: 'text-ink' }[accent] || 'text-ink'
  return (
    <div className="md:px-6 py-4 md:py-1 first:md:pl-0 last:md:pr-0">
      <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-3">
        {label}
      </div>
      <div className="flex items-baseline gap-2">
        <span className={`font-display font-light text-5xl md:text-6xl leading-none ${color}`}>
          {value}
        </span>
        {unit && <span className="font-mono text-xs text-ink-muted">{unit}</span>}
      </div>
    </div>
  )
}

function SubScoreBar({ label, value }) {
  const v = Math.max(0, Math.min(100, value))
  const color = v >= 75 ? 'bg-sage' : v >= 50 ? 'bg-amber' : 'bg-rust'
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <span className="font-mono text-[9px] tracking-[0.22em] uppercase text-ink-muted">{label}</span>
        <span className="font-mono text-[11px] text-ink">{Math.round(v)}</span>
      </div>
      <div className="h-1 bg-ink/10 overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${v}%` }} />
      </div>
    </div>
  )
}

function SimulationCard({ data }) {
  const pct = (n) => `${Math.round((n ?? 0) * 100)}%`
  const w = data?.winner || {}
  const ru = data?.runner_up || {}
  const fi = w.formula_inputs || {}

  return (
    <section className="rise border border-ink/30 p-6 md:p-8 fiber" style={{ animationDelay: '180ms' }}>
      <StageHeader num="02" title="Simulation" meta="Predicted performance" />

      {/* Formula synergy bars */}
      {fi.format_synergy != null && (
        <div className="mt-6 pb-6 border-b border-ink/20">
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-4">
            Interaction synergies · the inputs behind the numbers
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-5 md:gap-6">
            <SubScoreBar label="Format synergy" value={(fi.format_synergy / 1.5) * 100} />
            <SubScoreBar label="Goal synergy" value={(fi.goal_synergy / 1.5) * 100} />
            <SubScoreBar label="Audience synergy" value={(fi.audience_synergy / 1.5) * 100} />
            <SubScoreBar label="Feasibility" value={(w.feasibility ?? 0) * 100} />
            <SubScoreBar label="Consistency" value={(fi.signal_consistency ?? 0) * 100} />
          </div>
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 md:divide-x divide-ink/20">
        <MetricBlock
          label="Predicted reach"
          value={(w.predicted_reach ?? 0).toLocaleString()}
          unit="people"
          accent="blue"
        />
        <MetricBlock
          label="Engagement rate"
          value={(w.predicted_engagement ?? 0).toFixed(1)}
          unit="%"
          accent="amber"
        />
        <MetricBlock label="Model confidence" value={pct(w.confidence)} unit="" accent="sage" />
      </div>

      {/* Conversion + outcome score row */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 md:divide-x divide-ink/20">
        <MetricBlock
          label="Predicted conversion"
          value={(w.predicted_conversion ?? 0).toFixed(1)}
          unit="%"
          accent="sage"
        />
        <MetricBlock
          label="Outcome score"
          value={(w.outcome_score ?? 0).toFixed(2)}
          unit="/ 10"
          accent="amber"
        />
        <MetricBlock
          label="Complexity penalty"
          value={((w.complexity_penalty ?? 1) * 100).toFixed(1)}
          unit="%"
          accent="ink"
        />
      </div>

      {data?.score_breakdown?.length > 0 && (
        <div className="mt-8 pt-6 border-t border-ink/20">
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-3">
            How the simulation produced these numbers
          </div>
          <ul className="space-y-2">
            {data.score_breakdown.map((line, i) => (
              <li key={i} className="flex gap-3 text-sm leading-relaxed text-ink-soft">
                <span className="font-mono text-amber text-xs mt-1">→</span>
                <span className="font-display">{line}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-8 pt-6 border-t border-ink/20 grid grid-cols-1 md:grid-cols-3 gap-6">
        <DL label="Runner-up platform">{ru.platform || '—'}</DL>
        <DL label="Runner-up score">{(ru.outcome_score ?? 0).toFixed(2)}</DL>
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-1.5">
            Comparison
          </div>
          <p className="text-sm text-ink-soft leading-relaxed">{data?.comparison_summary || '—'}</p>
        </div>
      </div>
    </section>
  )
}

/* ── Content Card ────────────────────────────────────────────────────── */

function ContentCard({ data }) {
  return (
    <section className="rise border border-ink/30 p-6 md:p-8 fiber" style={{ animationDelay: '320ms' }}>
      <StageHeader num="03" title="Generation" meta="Platform-ready copy" />
      <div className="mt-6 space-y-6">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            Headline
          </div>
          <h4 className="font-display text-3xl md:text-[2.75rem] leading-[1.05] text-ink max-w-4xl">
            {data.headline}
          </h4>
        </div>
        <div className="relative border-l-2 border-amber pl-5 py-1">
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-3">
            Post copy
          </div>
          <p className="font-display text-lg leading-relaxed text-ink whitespace-pre-wrap max-w-3xl">
            {data.post_copy}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 pt-5 border-t border-ink/20">
          <div className="border border-ink px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.22em] bg-paper-2">
            <span className="text-amber mr-2">CTA</span>
            <span className="text-ink">{data.cta}</span>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-ink-muted">
            Tags
          </span>
          <div className="flex flex-wrap gap-2">
            {data.hashtags.map((h) => (
              <span
                key={h}
                className="font-mono text-xs text-blue hover:text-amber transition-colors cursor-default"
              >
                #{h}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

/* ── Feedback Card (structured) ──────────────────────────────────────── */

function CompareCell({ label, value, delta, positive, muted }) {
  return (
    <div className="border border-ink/20 p-4">
      <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted">
        {label}
      </div>
      <div
        className={`font-display font-light text-2xl mt-2 leading-none ${
          muted ? 'text-ink-muted' : 'text-ink'
        }`}
      >
        {value}
      </div>
      {delta !== undefined && (
        <div
          className={`font-mono text-[10px] mt-2 tracking-wider ${
            positive ? 'text-sage' : 'text-rust'
          }`}
        >
          {delta} vs predicted
        </div>
      )}
    </div>
  )
}

function FeedbackCard({ data, predicted }) {
  const predReach = predicted?.predicted_reach ?? 0
  const predEng = predicted?.predicted_engagement ?? 0
  const reachDelta = (data?.actual_reach ?? 0) - predReach
  const engDelta = (data?.actual_engagement ?? 0) - predEng
  const fmtInt = (n) => `${n >= 0 ? '+' : ''}${n.toLocaleString()}`
  const fmtPct = (n) => `${n >= 0 ? '+' : ''}${n.toFixed(1)}%`
  return (
    <section className="rise border border-ink/30 p-6 md:p-8 fiber" style={{ animationDelay: '460ms' }}>
      <StageHeader num="04" title="Feedback" meta="Closing the loop" />
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        <CompareCell
          label="Actual reach"
          value={(data?.actual_reach ?? 0).toLocaleString()}
          delta={fmtInt(reachDelta)}
          positive={reachDelta >= 0}
        />
        <CompareCell
          label="Actual engagement"
          value={`${(data?.actual_engagement ?? 0).toFixed(1)}%`}
          delta={fmtPct(engDelta)}
          positive={engDelta >= 0}
        />
        <CompareCell
          label="Predicted reach"
          value={predReach.toLocaleString()}
          muted
        />
        <CompareCell
          label="Predicted engagement"
          value={`${predEng.toFixed(1)}%`}
          muted
        />
      </div>

      {/* Structured strategy-update fields */}
      <div className="mt-8 pt-6 border-t border-ink/20 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            What worked
          </div>
          <p className="font-display text-base leading-snug text-ink flex gap-2">
            <span className="text-sage mt-0.5">✓</span>
            <span>{data.what_worked}</span>
          </p>
        </div>
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            What underperformed
          </div>
          <p className="font-display text-base leading-snug text-ink flex gap-2">
            <span className="text-rust mt-0.5">✗</span>
            <span>{data.what_underperformed}</span>
          </p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            Root cause
          </div>
          <p className="font-display italic text-base leading-snug text-ink-soft">
            &ldquo;{data.why_underperformed}&rdquo;
          </p>
        </div>
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            What should change
          </div>
          <p className="font-sans text-base leading-relaxed text-ink-soft">
            <span className="text-amber mr-1">→</span>
            {data.what_should_change}
          </p>
        </div>
      </div>

      {data.should_platform_change && (
        <div className="mt-6 border border-amber/30 bg-amber/5 p-4">
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-amber mb-2">
            ⚠ Platform change recommended
          </div>
          <p className="font-display text-sm leading-snug text-ink">
            {data.platform_change_reason}
          </p>
        </div>
      )}

      <div className="mt-6 pt-6 border-t border-ink/20 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            Learning note
          </div>
          <p className="font-display italic text-lg leading-snug text-ink">
            &ldquo;{data.learning_note}&rdquo;
          </p>
        </div>
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] uppercase text-ink-muted mb-2">
            Next recommendation
          </div>
          <p className="font-sans text-base leading-relaxed text-ink-soft">
            <span className="text-amber mr-1">→</span>
            {data.next_recommendation}
          </p>
        </div>
      </div>
    </section>
  )
}

/* ── Reasoning Chain ─────────────────────────────────────────────────── */

function ReasoningChain({ chain }) {
  if (!chain?.length) return null
  return (
    <section className="rise border border-ink/30 p-6 md:p-8 fiber" style={{ animationDelay: '560ms' }}>
      <StageHeader num="05" title="Reasoning Chain" meta="Full trace" />
      <ol className="mt-6 space-y-3">
        {chain.map((step, i) => (
          <li key={i} className="flex gap-4 text-sm leading-relaxed">
            <span className="font-mono text-[10px] tracking-[0.2em] text-amber mt-1 w-5 text-center flex-shrink-0">
              {i + 1}
            </span>
            <span className="font-display text-ink-soft">{step}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}

/* ── Error Card ──────────────────────────────────────────────────────── */

function ErrorCard({ message, onRetry }) {
  return (
    <div className="border-2 border-rust p-8 bg-paper-2">
      <div className="font-mono text-[10px] tracking-[0.3em] uppercase text-rust mb-3">
        Request failed
      </div>
      <p className="font-display text-xl text-ink mb-2">Could not reach the agent.</p>
      <p className="font-mono text-xs text-ink-soft mb-6 break-all">{message}</p>
      <p className="font-sans text-sm text-ink-soft mb-6 max-w-lg">
        Verify the backend is running at <code className="font-mono text-ink">{API_URL}</code> and
        that <code className="font-mono text-ink">GROQ_API_KEY</code> is set in <code className="font-mono text-ink">backend/.env</code>.
      </p>
      <button
        onClick={onRetry}
        className="font-mono text-[11px] uppercase tracking-[0.25em] border border-ink px-4 py-2 hover:bg-ink hover:text-paper transition-colors"
      >
        Dismiss · Retry
      </button>
    </div>
  )
}

function Footer() {
  return (
    <footer className="border-t border-ink/80 px-5 md:px-12 py-6 flex items-center justify-between gap-3 font-mono text-[10px] tracking-[0.28em] uppercase text-ink-soft">
      <span className="inline-flex items-center gap-2">
        <ReachCraftMark size={12} strokeWidth={2} ringOpacity={0.55} />
        ReachCraft
      </span>
      <span>© 2026</span>
    </footer>
  )
}

/* ─────────────────────────────────────────────────────────────────── */

export default function App() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const outputRef = useRef(null)
  const { theme, toggle: toggleTheme } = useTheme()

  const onSubmit = async (payload) => {
    setLoading(true)
    setError(null)
    setResult(null)
    outputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    try {
      const data = await runPipeline(payload)
      setResult(data)
    } catch (e) {
      setError(e.message || 'Unknown error')
    } finally {
      setLoading(false)
    }
  }
  const onRetry = () => setError(null)

  return (
    <div className="grain min-h-screen bg-paper text-ink">
      <div className="max-w-[1380px] mx-auto border-x border-ink/80 min-h-screen">
        <Header theme={theme} onToggleTheme={toggleTheme} />
        <Hero />

        <div className="grid grid-cols-1 md:grid-cols-12 border-b border-ink/80">
          <aside className="md:col-span-4 border-b md:border-b-0 md:border-r border-ink/80 p-6 md:p-10">
            <BriefForm onSubmit={onSubmit} loading={loading} />
          </aside>

          <main ref={outputRef} className="md:col-span-8 p-6 md:p-10 bg-paper-2/30">
            <div className="flex items-baseline justify-between mb-6 pb-3 border-b border-ink">
              <div className="flex items-baseline gap-4">
                <span className="font-mono text-[10px] tracking-[0.3em] uppercase text-ink-muted">
                  Output
                </span>
                <h2 className="font-display text-3xl font-light">Report</h2>
              </div>
              {result && (
                <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-sage">
                  · Complete
                </span>
              )}
              {loading && (
                <span className="font-mono text-[10px] tracking-[0.25em] uppercase text-amber">
                  · Running
                </span>
              )}
            </div>

            {!loading && !result && !error && <EmptyReport />}
            {loading && <LoadingReel />}
            {error && <ErrorCard message={error} onRetry={onRetry} />}
            {result && (
              <div className="space-y-6 md:space-y-8">
                {result.interpretation && <InterpretationCard data={result.interpretation} />}
                {result.decision && <DecisionCard data={result.decision} />}
                {result.simulation && <SimulationCard data={result.simulation} />}
                {result.content && <ContentCard data={result.content} />}
                {result.feedback && <FeedbackCard data={result.feedback} predicted={result.decision} />}
                {result.reasoning_chain && <ReasoningChain chain={result.reasoning_chain} />}
              </div>
            )}
          </main>
        </div>

        <Footer />
      </div>
    </div>
  )
}
