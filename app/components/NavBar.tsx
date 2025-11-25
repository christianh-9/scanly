import React from 'react'
import {Link} from "react-router"

const NavBar = () => {
    return (
        <nav className="navbar">
            <Link to="/">
                <p className="text-2xl font-bold text-gradient">Scanly</p>
            </Link>
            <Link to="/upload" className="primary-button w-fit">Upload Resume</Link>
        </nav>
    )
}
export default NavBar