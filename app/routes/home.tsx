import type { Route } from "./+types/home";
import NavBar from "~/components/NavBar";
import ResumeCard from "~/components/ResumeCard";
import { UploadIcon } from "~/components/Icons";
import { useEffect, useState } from "react";
import { usePuterStore } from "~/lib/puter";
import { Link, useNavigate } from "react-router";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Scanly" },
    { name: "description", content: "Blunt, specific feedback on your resume." },
  ];
}

export default function Home() {
    const { auth, isLoading, kv } = usePuterStore();
    const navigate = useNavigate()
    const [resumes, setResumes] = useState<Resume[]>([])
    const [loadingResumes, setLoadingResumes] = useState(true)

    useEffect(() => {
      if(!isLoading && !auth.isAuthenticated) navigate('/auth?next=/')
    }, [isLoading, auth.isAuthenticated])

    useEffect(() => {
      if(!auth.isAuthenticated) return
      const loadResumes = async () => {
        setLoadingResumes(true)

        const resumes = (await kv.list('resume:*', true)) as KVItem[];

        // skip records saved by older versions before analysis finished
        const parsedResumes = resumes
            ?.map((resume) => JSON.parse(resume.value) as Resume)
            .filter((resume) => typeof resume.feedback === 'object')
            .sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0))

        setResumes(parsedResumes || [])
        setLoadingResumes(false)
      }
      loadResumes()
    }, [auth.isAuthenticated])

  const removeResume = (id: string) => setResumes((all) => all.filter((r) => r.id !== id))

  return <main className="min-h-screen">
    <NavBar/>

    <section className="container-page py-10 sm:py-14">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Reviews</h1>
          <p className="mt-1 text-sm text-muted">
            {loadingResumes ? "Loading your reviews…"
              : resumes.length === 0 ? "Nothing reviewed yet."
              : `${resumes.length} ${resumes.length === 1 ? "resume" : "resumes"} reviewed`}
          </p>
        </div>
      </div>

      {loadingResumes && (
        <ul className="panel divide-y divide-line overflow-hidden" aria-hidden="true">
          {[0, 1, 2].map((i) => (
            <li key={i} className="flex items-center gap-4 px-4 py-3">
              <div className="h-[72px] w-14 animate-pulse rounded bg-hover" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-40 animate-pulse rounded bg-hover" />
                <div className="h-3 w-24 animate-pulse rounded bg-hover" />
              </div>
            </li>
          ))}
        </ul>
      )}

      {!loadingResumes && resumes.length > 0 && (
        <ul className="panel divide-y divide-line overflow-hidden">
          {resumes.map((resume) => (
            <ResumeCard key={resume.id} resume={resume} onDeleted={() => removeResume(resume.id)} />
          ))}
        </ul>
      )}

      {!loadingResumes && resumes.length === 0 && (
        <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed border-line-strong px-6 py-16 text-center">
          <div className="flex size-10 items-center justify-center rounded-full border border-line text-muted">
            <UploadIcon />
          </div>
          <div>
            <h2 className="font-medium">Upload your first resume</h2>
            <p className="mt-1 max-w-sm text-sm text-muted">
              Add the job you're applying for and Scanly scores your resume against it, without sugarcoating.
            </p>
          </div>
          <Link to="/upload" className="btn-primary">Start a review</Link>
        </div>
      )}
    </section>
  </main>
}
