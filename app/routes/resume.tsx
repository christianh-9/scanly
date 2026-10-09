import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import ATS from '~/components/ATS'
import DeleteResumeButton from '~/components/DeleteResumeButton'
import Details from '~/components/Details'
import { ArrowLeftIcon, ExternalIcon } from '~/components/Icons'
import NavBar from '~/components/NavBar'
import Summary from '~/components/Summary'
import { usePuterStore } from '~/lib/puter'

export const meta = () => ([
  {title: 'Scanly | Review'},
  {name: "description", content: "Your resume review"},
])

const ResumePage = () => {
    const {auth, isLoading, fs, kv} = usePuterStore()
    const {id} = useParams()
    const [resume, setResume] = useState<Resume | null>(null)
    const [imageUrl, setImageUrl] = useState('')
    const [resumeUrl, setResumeUrl] = useState('')
    const [notFound, setNotFound] = useState(false)
    const navigate = useNavigate()

    useEffect(() => {
      if(!isLoading && !auth.isAuthenticated) navigate(`/auth?next=/resume/${id}`)
    }, [isLoading, auth.isAuthenticated])

    useEffect(() => {
        if(!auth.isAuthenticated) return
        const urls: string[] = []
        const loadResume = async () => {
            const raw = await kv.get(`resume:${id}`)
            const data: Resume | null = raw ? JSON.parse(raw) : null
            if(typeof data?.feedback !== 'object') return setNotFound(true)
            setResume(data)

            const [pdfBlob, imageBlob] = await Promise.all([fs.read(data.resumePath), fs.read(data.imagePath)])
            if (pdfBlob) {
                const url = URL.createObjectURL(new Blob([pdfBlob], { type: 'application/pdf' }))
                urls.push(url)
                setResumeUrl(url)
            }
            if (imageBlob) {
                const url = URL.createObjectURL(imageBlob)
                urls.push(url)
                setImageUrl(url)
            }
        }
        loadResume()
        return () => urls.forEach(URL.revokeObjectURL)
    }, [id, auth.isAuthenticated])

    const feedback = resume?.feedback

    return (
        <main className="min-h-screen">
            <NavBar/>

            <div className="border-b border-line">
            <div className="container-page flex flex-wrap items-center justify-between gap-3 py-4">
                <div className="flex min-w-0 items-center gap-3">
                    <Link to="/" className="btn-icon" aria-label="Back to reviews"><ArrowLeftIcon/></Link>
                    <div className="min-w-0">
                        <h1 className="truncate font-semibold">{resume?.companyName || (resume ? 'Untitled review' : 'Review')}</h1>
                        {resume?.jobTitle && <p className="truncate text-sm text-muted">{resume.jobTitle}</p>}
                    </div>
                </div>
                {resume && <DeleteResumeButton resume={resume} variant="button" onDeleted={() => navigate('/')}/>}
            </div>
            </div>

            {notFound ? (
                <div className="container-page py-16 text-center">
                    <h2 className="font-semibold">Review not found</h2>
                    <p className="mt-1 text-sm text-muted">It was deleted, or its analysis didn't finish.</p>
                    <Link to="/upload" className="btn-primary mt-6">Start a new review</Link>
                </div>
            ) : (
                <div className="container-page grid gap-10 py-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:py-10">
                    <aside className="order-2 lg:order-none lg:sticky lg:top-24 lg:self-start">
                        <div className="panel overflow-hidden">
                            <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
                                <h2 className="text-sm font-medium">Resume</h2>
                                {resumeUrl && (
                                    <a href={resumeUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded text-sm text-muted hover:text-fg">
                                        Open PDF <ExternalIcon/>
                                    </a>
                                )}
                            </div>
                            <div className="aspect-[8.5/11] max-h-[60vh] bg-white lg:max-h-none">
                                {imageUrl
                                    ? <img src={imageUrl} alt="First page of the uploaded resume" className="size-full object-contain object-top"/>
                                    : <div className="size-full animate-pulse bg-hover"/>}
                            </div>
                        </div>
                    </aside>

                    {/* below lg this column dissolves so the resume can sit between the verdict and the details */}
                    <div className="contents lg:flex lg:flex-col lg:gap-8">
                        {feedback ? (
                            <>
                                <div className="order-1"><Summary feedback={feedback}/></div>
                                <div className="order-3 flex flex-col gap-8">
                                    <ATS score={feedback.ATS.score || 0} suggestions={feedback.ATS.tips || []}/>
                                    <Details feedback={feedback}/>
                                </div>
                            </>
                        ) : (
                            <div className="order-1 flex flex-col gap-4" aria-busy="true" aria-label="Loading review">
                                <div className="h-24 w-40 animate-pulse rounded bg-hover"/>
                                <div className="h-6 w-72 animate-pulse rounded bg-hover"/>
                                <div className="mt-4 h-40 animate-pulse rounded-lg bg-hover"/>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </main>
    )
}

export default ResumePage
