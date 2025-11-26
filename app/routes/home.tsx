import type { Route } from "./+types/home";
import NavBar from "~/components/NavBar";
import {resumes} from "../constants";
import ResumeCard from "~/components/ResumeCard";
import { useEffect } from "react";
import { usePuterStore } from "~/lib/puter";
import { useNavigate } from "react-router";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Scanly" },
    { name: "description", content: "Feedback for your next dream job!" },
  ];
}

export default function Home() {

    const { auth } = usePuterStore();  
    const navigate = useNavigate()

    useEffect(() => {
      if(!auth.isAuthenticated) navigate('/auth?next=/')
    }, [auth.isAuthenticated])

  return <main className="bg-[url('/images/bg-main.svg')] bg-cover"> 
    <NavBar/>

    <section className="main-section">
      <div className="page-heading py-16">
        <h1>Track your Applications and Resume Ratings</h1>
        <h2>Review your submissions and check AI feedback</h2>
      </div>

      {resumes.length > 0 && (
      <div className="resumes-section">
        {resumes.map((resume) => (
          <ResumeCard key={resume.id} resume={resume} />
        ))}
      </div>
      )}
    </section>
    
  </main>
}
