function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>

      <div className="stats">

        <div className="card">
          <h3>Total Resumes</h3>
          <p>124</p>
        </div>

        <div className="card">
          <h3>Top Matches</h3>
          <p>35</p>
        </div>

        <div className="card">
          <h3>Avg Score</h3>
          <p>72%</p>
        </div>

      </div>

    </div>
  );
}

export default Dashboard;