import { Link } from "react-router-dom";

function Navbar() {
  return (
    <div className="navbar">
      <Link to="/">Dashboard</Link>
      <Link to="/upload">Upload</Link>
      <Link to="/resumes">Resumes</Link>
      <Link to="/profile">Profile</Link>
    </div>
  );
}

export default Navbar;