import { cn, scoreTone, toneBg, toneText, verdict } from '~/lib/utils'

const CATEGORIES = [
    { key: 'ATS', label: 'ATS' },
    { key: 'toneAndStyle', label: 'Tone & style' },
    { key: 'content', label: 'Content' },
    { key: 'structure', label: 'Structure' },
    { key: 'skills', label: 'Skills' },
] as const

// The verdict: overall score, one plain sentence, then the five category bars.
// `where` finishes the flagged-changes line: "below" on a review page, elsewhere when previewed out of context
const Summary = ({ feedback, where = 'below' }: { feedback: Feedback; where?: string }) => {
    const score = feedback.overallScore
    const tone = scoreTone(score)
    const improveCount = CATEGORIES.reduce(
        (n, { key }) => n + feedback[key].tips.filter((t) => t.type === 'improve').length, 0)

    return (
        <section aria-labelledby="verdict" className="flex flex-col gap-8">
            <div>
                <p className="flex items-baseline gap-2">
                    <span className={cn('text-[clamp(4rem,10vw,6rem)] font-medium leading-none tracking-[-0.04em] num', toneText[tone])}>
                        {score}
                    </span>
                    <span className="text-xl text-subtle num">/100</span>
                </p>
                <h2 id="verdict" className="mt-3 text-2xl font-semibold tracking-tight text-balance">{verdict(score)}</h2>
                <p className="mt-1 text-sm text-muted">
                    {improveCount === 0 ? 'No changes flagged.' : `${improveCount} ${improveCount === 1 ? 'change' : 'changes'} flagged ${where}.`}
                </p>
            </div>

            <ul className="flex flex-col gap-3.5">
                {CATEGORIES.map(({ key, label }, i) => {
                    const s = feedback[key].score
                    const t = scoreTone(s)
                    return (
                        <li key={key} className="grid grid-cols-[110px_1fr_36px] items-center gap-4 text-sm">
                            <span className="text-muted">{label}</span>
                            <span className="h-1.5 overflow-hidden rounded-full bg-line" aria-hidden="true">
                                <span
                                    className={cn('bar-fill block h-full rounded-full', toneBg[t])}
                                    style={{ width: `${s}%`, animationDelay: `${i * 70}ms` }}
                                />
                            </span>
                            <span className={cn('text-right num', toneText[t])}>{s}</span>
                        </li>
                    )
                })}
            </ul>
        </section>
    )
}

export default Summary
