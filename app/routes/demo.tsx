import { Link } from 'react-router'
import NavBar from '~/components/NavBar'
import ReviewView from '~/components/ReviewView'
import { DEMO_RESUME } from '~/lib/demo'

export const meta = () => ([
    { title: 'Scanly | Sample review' },
    { name: 'description', content: 'A sample Scanly review of a fictional resume.' },
])

// Public sample review: static data, no sign-in, no API calls.
const Demo = () => (
    <main className="min-h-screen">
        <NavBar/>
        <div className="border-b border-line bg-raised">
            <div className="container-page flex flex-wrap items-center justify-between gap-3 py-3">
                <p className="text-sm text-muted">
                    This is a sample review of a <span className="text-fg">fictional resume</span>, scored against a software engineer job.
                </p>
                <Link to="/auth?next=/upload" className="btn-primary h-8 px-3">Review your resume</Link>
            </div>
        </div>
        <ReviewView
            title="Sample review"
            subtitle={`${DEMO_RESUME.jobTitle} · fictional resume`}
            backTo="/"
            backLabel="Back to home"
            imageUrl={DEMO_RESUME.imagePath}
            pdfUrl={DEMO_RESUME.resumePath}
            feedback={DEMO_RESUME.feedback}
        />
    </main>
)

export default Demo
