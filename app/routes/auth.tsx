import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router";
import { LogoMark, SpinnerIcon } from "~/components/Icons";
import { usePuterStore } from "~/lib/puter";

export const meta = () => ([
  {title: 'Scanly | Sign in'},
  {name: "description", content: "Sign in to Scanly"},
])

const Auth = () => {
    const { isLoading, error, auth } = usePuterStore();
    const location = useLocation()
    const next = new URLSearchParams(location.search).get('next') || '/'
    const navigate = useNavigate()

    useEffect(() => {
      if(auth.isAuthenticated) navigate(next)
    }, [auth.isAuthenticated, next])

    return (
      <main className="flex min-h-screen items-center justify-center px-4">
        <div className="flex w-full max-w-sm flex-col items-center text-center">
          <LogoMark width={32} height={32}/>
          <h1 className="mt-6 text-2xl font-semibold tracking-tight">Sign in to Scanly</h1>
          <p className="mt-2 text-sm text-muted">
            Your resumes and reviews are stored in your Puter account. Resumes are sent to Google Gemini for analysis.
          </p>

          <button
            className="btn-primary mt-8 h-10 w-full"
            onClick={auth.isAuthenticated ? auth.signOut : auth.signIn}
            disabled={isLoading}
          >
            {isLoading && <SpinnerIcon/>}
            {isLoading ? "Checking your session…" : auth.isAuthenticated ? "Sign out" : "Continue with Puter"}
          </button>

          {error && <p role="alert" className="mt-4 text-sm text-fail">{error}</p>}
        </div>
      </main>
    )
  }

export default Auth
