import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import FileUploader from '~/components/FileUploader'
import { AlertIcon, CheckIcon, SpinnerIcon } from '~/components/Icons'
import NavBar from '~/components/NavBar'
import { convertPdfToImage } from '~/lib/pdf2img'
import { usePuterStore } from '~/lib/puter'
import { cn, generateUUID } from '~/lib/utils'
import { API_URL, wakeBackend } from '~/lib/api'

export const meta = () => ([
    { title: 'Scanly | New review' },
    { name: 'description', content: 'Upload a resume for a blunt, specific review.' },
])

type StepStatus = 'pending' | 'active' | 'done' | 'error'
interface Step { label: string; status: StepStatus; ms?: number }

const STEPS = ['Rendering first page', 'Analyzing resume', 'Uploading PDF', 'Uploading preview', 'Saving review']

const Upload = () => {
    const {auth, isLoading, fs, kv} = usePuterStore()
    const navigate = useNavigate()
    const [steps, setSteps] = useState<Step[] | null>(null)
    const [error, setError] = useState('')
    const [file, setFile] = useState<File | null>(null)
    const stepStart = useRef(0)
    const runStart = useRef(0)
    const logRef = useRef<HTMLElement>(null)
    const [now, setNow] = useState(0)

    useEffect(() => {
        if(!isLoading && !auth.isAuthenticated) navigate('/auth?next=/upload')
    }, [isLoading, auth.isAuthenticated])

    // wake the backend while the form is being filled in
    useEffect(wakeBackend, [])

    const isProcessing = steps !== null && !error

    // live clock for the active step and the run total
    useEffect(() => {
        if (!isProcessing) return
        const t = setInterval(() => setNow(performance.now()), 100)
        return () => clearInterval(t)
    }, [isProcessing])

    // marks step i active and everything before it done, recording how long the previous step took
    const advance = (i: number) => {
        const now = performance.now()
        const elapsed = now - stepStart.current // read before the ref moves; the updater below runs later
        setSteps((s) => s && s.map((step, j) =>
            j === i - 1 ? { ...step, status: 'done', ms: elapsed }
            : j === i ? { ...step, status: 'active' }
            : step))
        stepStart.current = now
    }

    const analyze = async ({ companyName, jobTitle, jobDescription, file}: {companyName : string, jobTitle: string, jobDescription:string, file: File}) => {
        advance(0)
        const imageFile = await convertPdfToImage(file)
        if(!imageFile.file) throw new Error(imageFile.error || "Couldn't read that PDF. Check it opens, then try again.")

        advance(1)
        const body = new FormData()
        body.append('resume', file)
        body.append('jobTitle', jobTitle)
        body.append('jobDescription', jobDescription)
        const res = await fetch(`${API_URL}/api/analyze`, { method: 'POST', body })
        if (!res.ok) {
            const detail = await res.json().then((d) => d.detail).catch(() => null)
            throw new Error(detail || `Analysis failed (${res.status}). Is the backend running?`)
        }
        const feedback: Feedback = await res.json()

        advance(2)
        const uploadedFile = await fs.upload([file])
        if (!uploadedFile) throw new Error("Couldn't upload the PDF to your Puter storage.")

        advance(3)
        const uploadedImage = await fs.upload([imageFile.file])
        if (!uploadedImage) throw new Error("Couldn't upload the preview image.")

        advance(4)
        const uuid = generateUUID()
        const data: Resume = {
            id: uuid,
            resumePath: uploadedFile.path,
            imagePath: uploadedImage.path,
            companyName, jobTitle,
            feedback,
            createdAt: Date.now(),
        }
        await kv.set(`resume:${uuid}`, JSON.stringify(data))
        advance(5)
        navigate(`/resume/${uuid}`)
    }

    const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        const formData = new FormData(e.currentTarget)
        const companyName = (formData.get('company-name') as string).trim()
        const jobTitle = (formData.get('job-title') as string).trim()
        const jobDescription = (formData.get('job-description') as string).trim()

        if(!file) return setError("Choose a PDF resume first.")

        setError('')
        setSteps(STEPS.map((label) => ({ label, status: 'pending' })))
        runStart.current = stepStart.current = performance.now()
        setNow(runStart.current)
        // on phones the log sits below the form; bring it into view
        logRef.current?.scrollIntoView({ block: 'nearest', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
        try {
            await analyze({ companyName, jobTitle, jobDescription, file })
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err))
            setSteps((s) => s && s.map((step) => step.status === 'active' ? { ...step, status: 'error' } : step))
        }
    }

  return (
    <main className="min-h-screen">
        <NavBar/>

        <section className="container-page py-10 sm:py-14">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">New review</h1>
            <p className="mt-1 max-w-[60ch] text-sm text-muted">
                Upload a PDF. Add the job you're applying for and the review is scored against it; leave it blank for a general review.
            </p>

            <div className="mt-8 grid gap-10 lg:grid-cols-[minmax(0,1fr)_340px]">
            <div>
                <form id="upload-form" onSubmit={handleSubmit} className="flex flex-col gap-5">
                    <fieldset disabled={isProcessing} className="contents">
                        <div className="grid gap-5 sm:grid-cols-2">
                            <div className="flex flex-col gap-2">
                                <label htmlFor="company-name" className="field-label">Company</label>
                                <input className="field" type="text" name="company-name" id="company-name" placeholder="Acme Inc." autoComplete="organization"/>
                            </div>
                            <div className="flex flex-col gap-2">
                                <label htmlFor="job-title" className="field-label">Job title</label>
                                <input className="field" type="text" name="job-title" id="job-title" placeholder="Frontend Engineer" autoComplete="off"/>
                            </div>
                        </div>
                        <div className="flex flex-col gap-2">
                            <label htmlFor="job-description" className="field-label">Job description</label>
                            <textarea className="field min-h-36 resize-y" rows={6} name="job-description" id="job-description" placeholder="Paste the posting. The more specific, the more specific the feedback."/>
                        </div>
                        <div className="flex flex-col gap-2">
                            <label htmlFor="resume-file" className="field-label">Resume</label>
                            <FileUploader onFileSelect={(f) => { setFile(f); setError('') }} disabled={isProcessing}/>
                        </div>
                    </fieldset>

                    {error && !steps && <p role="alert" className="text-sm text-fail">{error}</p>}

                    <div className="flex justify-end border-t border-line pt-5">
                        <button className="btn-primary" type="submit" disabled={isProcessing}>
                            {isProcessing && <SpinnerIcon/>}
                            {isProcessing ? 'Analyzing…' : error && steps ? 'Try again' : 'Analyze resume'}
                        </button>
                    </div>
                </form>
            </div>

            <aside ref={logRef} aria-live="polite" className="scroll-mt-20">
                <div className="panel overflow-hidden">
                    <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
                        <h2 className="text-sm font-medium">Analysis log</h2>
                        {steps && (
                            <span className={cn('text-xs', error ? 'text-fail' : 'text-muted')}>
                                {error ? 'Failed' : 'Running'}
                                {isProcessing && <span className="num"> · {((now - runStart.current) / 1000).toFixed(1)}s</span>}
                            </span>
                        )}
                    </div>
                    <ol className="flex flex-col py-2">
                            {(steps ?? STEPS.map((label): Step => ({ label, status: 'pending' }))).map((step) => (
                                <li key={step.label} className={cn('flex items-center gap-3 px-4 py-1.5 text-sm',
                                    step.status === 'pending' && 'text-subtle',
                                    step.status === 'error' && 'text-fail')}>
                                    <span className="flex size-4 items-center justify-center">
                                        {step.status === 'done' && <CheckIcon className="text-pass"/>}
                                        {step.status === 'active' && <SpinnerIcon className="text-fg"/>}
                                        {step.status === 'error' && <AlertIcon/>}
                                        {step.status === 'pending' && <span className="size-1.5 rounded-full bg-line-strong"/>}
                                    </span>
                                    <span className="flex-1">{step.label}</span>
                                    {step.ms !== undefined && <span className="text-xs text-subtle num">{(step.ms / 1000).toFixed(1)}s</span>}
                                    {step.status === 'active' && <span className="text-xs text-muted num">{((now - stepStart.current) / 1000).toFixed(1)}s</span>}
                                </li>
                            ))}
                    </ol>
                    {!steps && <p className="border-t border-line px-4 py-3 text-xs text-subtle">Analysis can take up to a minute.</p>}
                    {error && steps && (
                        <p role="alert" className="border-t border-line px-4 py-3 text-sm text-fail">{error}</p>
                    )}
                </div>
            </aside>
            </div>
        </section>
    </main>
  )
}

export default Upload
