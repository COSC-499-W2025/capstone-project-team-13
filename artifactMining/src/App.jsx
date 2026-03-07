import { BrowserRouter, Routes, Route } from "react-router-dom";

import Navbar from "./components/Navbar";

import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Resumes from "./pages/Resumes";

function App() {
  return (
    <BrowserRouter>

      <Navbar />

      <div className="page-container">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/resumes" element={<Resumes />} />
        </Routes>
      </div>

    </BrowserRouter>
  );
}

export default App;