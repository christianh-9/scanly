import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import FileUploader from '~/components/FileUploader'
import NavBar from '~/components/NavBar'
import { convertPdfToImage } from '~/lib/pdf2img'
import { usePuterStore } from '~/lib/puter'
import { generateUUID } from '~/lib/utils'

const Upload = () => {
    const {auth, isLoading, fs, kv} = usePuterStore()
    const navigate = useNavigate()
    const [isProcessing, setIsProcessing] = useState(false)
    const [statusText, setStatusText] = useState('')
    const [error, setError] = useState('')
    const [file, setFile] = useState<File | null>(null)

    useEffect(() => {
        if(!isLoading && !auth.isAuthenticated) navigate('/auth?next=/upload')
    }, [isLoading, auth.isAuthenticated])

    const handleFileSelect = (file: File | null) => {
        setFile(file)
    }

    const analyze = async ({ companyName, jobTitle, jobDescription, file}: {companyName : string, jobTitle: string, jobDescription:string, file: File}) => {
        setStatusText("Converting to image...")
        const imageFile = await convertPdfToImage(file)
        if(!imageFile.file) throw new Error(imageFile.error || "Failed to convert PDF to image")

        setStatusText("Analyzing...")
        const body = new FormData()
        body.append('resume', file)
        body.append('jobTitle', jobTitle)
        body.append('jobDescription', jobDescription)
        const res = await fetch('/api/analyze', { method: 'POST', body })
        if (!res.ok) {
            const detail = await res.json().then((d) => d.detail).catch(() => null)
            throw new Error(detail || `Analysis failed (${res.status}). Is the backend running?`)
        }
        const feedback: Feedback = await res.json()

        setStatusText("Uploading the file...")
        const uploadedFile = await fs.upload([file])
        if (!uploadedFile) throw new Error("Failed to upload file")

        setStatusText("Uploading the image...")
        const uploadedImage = await fs.upload([imageFile.file])
        if (!uploadedImage) throw new Error("Failed to upload image")

        const uuid = generateUUID()
        const data: Resume = {
            id: uuid,
            resumePath: uploadedFile.path,
            imagePath: uploadedImage.path,
            companyName, jobTitle,
            feedback,
        }
        await kv.set(`resume:${uuid}`, JSON.stringify(data))
        setStatusText("Analysis complete, redirecting...")
        navigate(`/resume/${uuid}`)
    }

    const handleAnalyze = async (args: Parameters<typeof analyze>[0]) => {
        setIsProcessing(true)
        setError('')
        try {
            await analyze(args)
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err))
            setIsProcessing(false)
        }
    }

    const handleSubmit =(e: FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        const form = e.currentTarget.closest('form')
        if (!form) return
        const formData = new FormData(form)

        const companyName = formData.get('company-name') as string 
        const jobTitle = formData.get('job-title') as string
        const jobDescription = formData.get('job-description') as string

        if(!file) return setError("Please choose a PDF resume first")

        handleAnalyze({ companyName, jobTitle, jobDescription, file})
    }   

  return (
    <main className="bg-[url('/images/bg-main.svg')] bg-cover"> 
        <NavBar/>

        <section className="main-section">
            <div className="page-heading py-16">
                <h1>Smart feedback for your dream job</h1>
                {isProcessing ? (
                    <> 
                        <h2>{statusText}</h2>
                        <img src="/images/resume-scan.gif" className="w-full"/>
                    </>
                ) : (
                    <h2>Drop your resume for an ATS score and tips for improvement</h2>
                )} 
                {error && <p className="text-red-600 text-lg mt-4">{error}</p>}
                {!isProcessing && (
                    <form id="upload-form" onSubmit ={handleSubmit} className="flex flex-col gap-4 mt-8">
                        <div className="form-div">
                            <label htmlFor="company-name">Company Name</label>
                            <input type="text" name="company-name" placeholder="Company Name" id="company-name"/>
                        </div>
                        <div className="form-div">
                            <label htmlFor="job-title">Job title</label>
                            <input type="text" name="job-title" placeholder="Job Title" id="job-title"/>
                        </div>
                        <div className="form-div">
                            <label htmlFor="job-description">Job Description</label>
                            <textarea rows={5} name="job-description" placeholder="Job Description" id="job-description"/>
                        </div>
                        <div className="form-div">
                            <label>Upload Resume</label>
                            <FileUploader onFileSelect={handleFileSelect}/>
                        </div>

                        <button className="primary-button" type="submit">
                            Analyze Resume
                        </button>
                    </form>
                )}
            </div>
        </section>
    </main>
  )
}

export default Upload