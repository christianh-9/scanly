import { useEffect } from 'react'
import { Link } from 'react-router'
import { wakeBackend } from '~/lib/api'
import Summary from '~/components/Summary'
import { DEMO_RESUME } from '~/lib/demo'

const STEPS = [
    { title: 'Upload your resume', body: 'Any PDF up to 20 MB. Scanned resumes work too.' },
    { title: 'Add the job you want', body: 'Paste the posting to get feedback against it, or skip it for a general review.' },
    { title: 'Read the verdict', body: 'You get a score out of 100 for the whole resume and for each category, with the changes to make first.' },
]

// Front page for signed-out visitors. The preview on the right is the real sample review, not a mockup.
const Landing = () => {
    useEffect(wakeBackend, [])  // most visitors land here first

    return (
    <>
        <section className="container-page grid items-center gap-12 py-14 sm:py-20 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <div className="flex flex-col items-start gap-6">
                <h1 className="max-w-[16ch] text-4xl font-semibold leading-[1.08] tracking-[-0.03em] text-balance sm:text-5xl">
                    Find out what's wrong with your resume before a recruiter does.
                </h1>
                <p className="max-w-[52ch] text-base leading-relaxed text-muted sm:text-lg">
                    Upload your resume and the job you want. Scanly scores it across ATS, tone, content, structure
                    and skills, and tells you plainly what to fix.
                </p>
                <div className="flex flex-wrap gap-3">
                    <Link to="/demo" className="btn-primary h-10 px-5">See a sample review</Link>
                    <Link to="/auth?next=/upload" className="btn-secondary h-10 px-5">Review your resume</Link>
                </div>
            </div>

            {/* the sample review, previewed: resume on top with a single scan pass, verdict below */}
            <div className="panel overflow-hidden">
                <div className="relative h-44 overflow-hidden border-b border-line bg-white sm:h-52">
                    <img src={DEMO_RESUME.imagePath} alt="" className="w-full object-cover object-top"/>
                    <div className="scan-line" aria-hidden="true"/>
                </div>
                <div className="p-5 sm:p-6">
                    <Summary feedback={DEMO_RESUME.feedback} where="in the full review"/>
                    <Link to="/demo" className="mt-6 inline-block rounded text-sm text-muted hover:text-fg">
                        Open the full sample review →
                    </Link>
                </div>
            </div>
        </section>

        <section className="border-t border-line">
            <div className="container-page py-14">
                <h2 className="text-sm font-medium text-muted">How it works</h2>
                <ol className="mt-6 grid gap-8 sm:grid-cols-3">
                    {STEPS.map((step, i) => (
                        <li key={step.title} className="flex flex-col gap-2">
                            <span className="num text-sm text-subtle">{i + 1}</span>
                            <h3 className="font-semibold">{step.title}</h3>
                            <p className="text-sm leading-relaxed text-muted">{step.body}</p>
                        </li>
                    ))}
                </ol>
            </div>
        </section>

        <footer className="border-t border-line">
            <div className="container-page flex flex-wrap items-center justify-between gap-3 py-6 text-sm text-subtle">
                <p>Scanly sends your resume to Google Gemini for analysis and saves the review in your own Puter account.</p>
                <a href="https://github.com/christianh-9/scanly" target="_blank" rel="noopener noreferrer" className="hover:text-fg">
                    Source on GitHub
                </a>
            </div>
        </footer>
    </>
    )
}

export default Landing
