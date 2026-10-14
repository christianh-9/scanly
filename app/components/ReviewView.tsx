import type { ReactNode } from 'react'
import { Link } from 'react-router'
import ATS from '~/components/ATS'
import Details from '~/components/Details'
import { ArrowLeftIcon, ExternalIcon } from '~/components/Icons'
import Summary from '~/components/Summary'

interface Props {
    title: string
    subtitle?: string
    backTo: string
    backLabel: string
    imageUrl: string
    pdfUrl: string
    feedback: Feedback | null
    actions?: ReactNode  // right side of the header strip, e.g. the delete button
}

// The review layout shared by real reviews (/resume/:id) and the public sample (/demo).
const ReviewView = ({ title, subtitle, backTo, backLabel, imageUrl, pdfUrl, feedback, actions }: Props) => (
    <>
        <div className="border-b border-line">
            <div className="container-page flex flex-wrap items-center justify-between gap-3 py-4">
                <div className="flex min-w-0 items-center gap-3">
                    <Link to={backTo} className="btn-icon" aria-label={backLabel}><ArrowLeftIcon/></Link>
                    <div className="min-w-0">
                        <h1 className="truncate font-semibold">{title}</h1>
                        {subtitle && <p className="truncate text-sm text-muted">{subtitle}</p>}
                    </div>
                </div>
                {actions}
            </div>
        </div>

        <div className="container-page grid gap-10 py-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:py-10">
            <aside className="order-2 lg:order-none lg:sticky lg:top-24 lg:self-start">
                <div className="panel overflow-hidden">
                    <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
                        <h2 className="text-sm font-medium">Resume</h2>
                        {pdfUrl && (
                            <a href={pdfUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded text-sm text-muted hover:text-fg">
                                Open PDF <ExternalIcon/>
                            </a>
                        )}
                    </div>
                    <div className="aspect-[8.5/11] max-h-[60vh] bg-white lg:max-h-none">
                        {imageUrl
                            ? <img src={imageUrl} alt="First page of the resume" className="size-full object-contain object-top"/>
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
    </>
)

export default ReviewView
