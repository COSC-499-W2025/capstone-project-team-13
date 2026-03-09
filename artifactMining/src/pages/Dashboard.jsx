import React from 'react'
function Dashboard() {
  return (
    <div className="dashboard-grid">

      <div className="card projects">
        <h2>Projects</h2>
        <p>Uploaded projects will appear here.</p>
      </div>

      <div className="card resumes">
        <h2>AI Generated Resumes</h2>
      </div>

      <div className="card portfolios">
        <h2>AI Generated Portfolios</h2>
      </div>

      <div className="card insights">
        <h2>Charts & Insights</h2>
      </div>

    </div>
  );
}

export default Dashboard;
