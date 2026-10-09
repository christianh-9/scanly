import { Link, useLocation } from "react-router";
import { LogoMark, PlusIcon } from "./Icons";

const NavBar = () => {
    const { pathname } = useLocation();

    return (
        <header className="sticky top-0 z-10 border-b border-line bg-bg/80 backdrop-blur-md">
            <nav className="container-page flex h-14 items-center justify-between">
                <Link to="/" className="flex items-center gap-2 rounded-md text-base font-semibold tracking-tight">
                    <LogoMark />
                    Scanly
                </Link>
                {pathname !== "/upload" && (
                    <Link to="/upload" className="btn-primary h-8 px-3">
                        <PlusIcon /> New review
                    </Link>
                )}
            </nav>
        </header>
    );
};

export default NavBar;
