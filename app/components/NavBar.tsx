import { Link, useLocation, useNavigate } from "react-router";
import { usePuterStore } from "~/lib/puter";
import { LogoMark, PlusIcon } from "./Icons";

const NavBar = () => {
    const { pathname } = useLocation();
    const navigate = useNavigate();
    const { auth, isLoading } = usePuterStore();
    const signedOut = !isLoading && !auth.isAuthenticated;
    const signedIn = !isLoading && auth.isAuthenticated;

    const signOut = async () => {
        await auth.signOut();
        navigate("/");  // signed-out visitors see the front page
    };

    return (
        <header className="sticky top-0 z-10 border-b border-line bg-bg/80 backdrop-blur-md">
            <nav className="container-page flex h-14 items-center justify-between gap-3">
                <Link to="/" className="flex items-center gap-2 rounded-md text-base font-semibold tracking-tight">
                    <LogoMark />
                    Scanly
                </Link>
                {signedOut && <Link to="/auth?next=/" className="btn-secondary h-8 px-3">Sign in</Link>}
                {signedIn && (
                    <div className="flex items-center gap-2">
                        {auth.user?.username && (
                            <span className="hidden max-w-40 truncate text-sm text-subtle sm:inline">{auth.user.username}</span>
                        )}
                        <button type="button" onClick={signOut} className="btn h-8 px-3 text-muted hover:bg-hover hover:text-fg">
                            Sign out
                        </button>
                        {pathname !== "/upload" && (
                            <Link to="/upload" className="btn-primary h-8 px-3">
                                <PlusIcon /> New review
                            </Link>
                        )}
                    </div>
                )}
            </nav>
        </header>
    );
};

export default NavBar;
