import { Link, useNavigate } from "react-router-dom";

function Dashboard() {

  const navigate = useNavigate();

  const user = JSON.parse(
    localStorage.getItem("borderguardUser")
  );

  const logout = () => {
    localStorage.removeItem("borderguardUser");
    navigate("/login");
  };

  return (
    <div className="dashboard">

      {/* Sidebar */}

      <aside className="sidebar">

        <div className="sidebar-logo">

          <div className="logo-shield">
            🛡️
          </div>

          <div>
            <h2>BorderGuard</h2>
            <small>AI SECURITY</small>
          </div>

        </div>

        <nav>

          <Link className="active" to="/dashboard">
            🏠 Dashboard
          </Link>

          <Link to="/screening">
            🔍 New Screening
          </Link>

          <Link to="/history">
            🕘 Screening History
          </Link>

          <Link to="/result">
            📊 Reports
          </Link>

          <Link to="/profile">
            ⚙️ Profile
          </Link>

        </nav>

        <button
          className="logout-btn"
          onClick={logout}
        >
          ↪ Logout
        </button>

      </aside>

      {/* Main */}

      <main className="main-content">

        <header className="topbar">

          <div>
            <p>SECURITY CONTROL CENTER</p>
            <h1>Good morning, {user?.name}</h1>
          </div>

          <div className="officer">
            <div className="avatar">
              {user?.name?.charAt(0)}
            </div>

            <div>
              <strong>{user?.name}</strong>
              <small>Screening Officer</small>
            </div>
          </div>

        </header>

        {/* Stats */}

        <section className="stats-grid">

          <div className="stat-card">
            <span>Total Screenings</span>
            <strong>1,284</strong>
            <small>Today: +24</small>
          </div>

          <div className="stat-card danger">
            <span>High Risk</span>
            <strong>37</strong>
            <small>Requires review</small>
          </div>

          <div className="stat-card warning">
            <span>Medium Risk</span>
            <strong>89</strong>
            <small>Under monitoring</small>
          </div>

          <div className="stat-card success">
            <span>Low Risk</span>
            <strong>1,158</strong>
            <small>Verified</small>
          </div>

        </section>

        {/* Main Screening Card */}

        <section className="welcome-screen">

          <div>

            <span className="section-label">
              AI DOCUMENT SCREENING
            </span>

            <h2>
              Verify a document in seconds.
            </h2>

            <p>
              Upload a passport, visa, ID card or permit.
              BorderGuard AI will analyze the document
              for identity and security risks.
            </p>

            <Link
              to="/screening"
              className="primary-btn inline-btn"
            >
              Start New Screening →
            </Link>

          </div>

          <div className="shield-large">
            🛡️
          </div>

        </section>

        {/* Recent */}

        <section className="recent-section">

          <div className="section-header">
            <h2>Recent Screenings</h2>

            <Link to="/history">
              View all →
            </Link>
          </div>

          <div className="screening-table">

            <div className="table-head">
              <span>Document</span>
              <span>Type</span>
              <span>Risk</span>
              <span>Score</span>
              <span>Status</span>
            </div>

            <div className="table-row">
              <span>Passport #A7821</span>
              <span>Passport</span>
              <span className="risk high">HIGH</span>
              <span>86/100</span>
              <span>⚠ Review</span>
            </div>

            <div className="table-row">
              <span>Visa #V9211</span>
              <span>Visa</span>
              <span className="risk medium">MEDIUM</span>
              <span>48/100</span>
              <span>Monitoring</span>
            </div>

            <div className="table-row">
              <span>ID #ID8812</span>
              <span>National ID</span>
              <span className="risk low">LOW</span>
              <span>18/100</span>
              <span>✓ Verified</span>
            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;