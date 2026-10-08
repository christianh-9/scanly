import type { Route } from "./+types/home";
import NavBar from "~/components/NavBar";
import ResumeCard from "~/components/ResumeCard";
import { useEffect, useState } from "react";
import { usePuterStore } from "~/lib/puter";
import { Link, useNavigate } from "react-router";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Scanly" },
    { name: "description", content: "Feedback for your next dream job!" },
  ];
}

export default function Home() {

    const { auth, isLoading, kv } = usePuterStore();
    const navigate = useNavigate()
    const [resumes, setResumes] = useState<Resume[]>([])
    const [loadingResumes, setLoadingResumes] = useState(false)
  
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

        setResumes(parsedResumes || [])
        setLoadingResumes(false)
      }
      loadResumes()
    }, [auth.isAuthenticated])

  return <main className="bg-[url('/images/bg-main.svg')] bg-cover"> 
    <NavBar/>

    <section className="main-section">
      <div className="page-heading py-16">
        <h1>Track your Applications and Resume Ratings</h1>
        {!loadingResumes && resumes?.length === 0 ? (
          <h2>No Resumes found. Upload your first resume for feedback.</h2>
        ) : (
          <h2>Review your submissions and check AI feedback</h2>
        )}
        </div>
        {loadingResumes && (
          <div className="flex flex-col items-center justify-center">
            <img src="/images/resume-scan-2.gif" className="w-[200px]"/>
          </div>
        )}

      {!loadingResumes && resumes.length > 0 && (
      <div className="resumes-section">
        {resumes.map((resume) => (
          <ResumeCard key={resume.id} resume={resume} />
        ))}
      </div>
      )}
      {!loadingResumes && resumes?.length === 0 && (
        <div className="flex flex-col items-center justify-center mt-10 gap-4">
          <Link to="/upload" className ="primary-button w-fit text-xl font-semibold">
            Upload Resume
          </Link>
          

        </div>
      )}
    </section>
    
  </main>
}
