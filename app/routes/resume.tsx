import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import DeleteResumeButton from '~/components/DeleteResumeButton'
import NavBar from '~/components/NavBar'
import ReviewView from '~/components/ReviewView'
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

    return (
        <main className="min-h-screen">
            <NavBar/>
            {notFound ? (
                <div className="container-page py-16 text-center">
                    <h2 className="font-semibold">Review not found</h2>
                    <p className="mt-1 text-sm text-muted">It was deleted, or its analysis didn't finish.</p>
                    <Link to="/upload" className="btn-primary mt-6">Start a new review</Link>
                </div>
            ) : (
                <ReviewView
                    title={resume?.companyName || (resume ? 'Untitled review' : 'Review')}
                    subtitle={resume?.jobTitle}
                    backTo="/"
                    backLabel="Back to reviews"
                    imageUrl={imageUrl}
                    pdfUrl={resumeUrl}
                    feedback={resume?.feedback ?? null}
                    actions={resume && <DeleteResumeButton resume={resume} variant="button" onDeleted={() => navigate('/')}/>}
                />
            )}
        </main>
    )
}

export default ResumePage
