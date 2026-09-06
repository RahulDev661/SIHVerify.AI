import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getStoredUser, logout as logoutSession, getHistory } from "../api";

function Dashboard() {

  const navigate = useNavigate();

  const user = getStoredUser();

  const [recent, setRecent] = useState([]);
  const [stats, setStats] = useState({ total: 0, high: 0, medium: 0, low: 0 });
  const [loadingHistory, setLoadingHistory] = useState(true);

  useEffect(() => {
    getHistory(200)
      .then((records) => {
        setRecent(records.slice(0, 5));
        setStats({
          total: records.length,
          high: records.filter((r) => r.risk === "HIGH").length,
          medium: records.filter((r) => r.risk === "MEDIUM").length,
          low: records.filter((r) => r.risk === "LOW").length,
        });
      })
      .catch(() => {
        // Leave stats/recent at their empty defaults on failure.
      })
      .finally(() => setLoadingHistory(false));
  }, []);

  const logout = () => {
    logoutSession();
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
            <strong>{stats.total}</strong>
            <small>All time</small>
          </div>

          <div className="stat-card danger">
            <span>High Risk</span>
            <strong>{stats.high}</strong>
            <small>Requires review</small>
          </div>

          <div className="stat-card warning">
            <span>Medium Risk</span>
            <strong>{stats.medium}</strong>
            <small>Under monitoring</small>
          </div>

          <div className="stat-card success">
            <span>Low Risk</span>
            <strong>{stats.low}</strong>
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

            {loadingHistory && (
              <div className="table-row">
                <span>Loading…</span>
              </div>
            )}

            {!loadingHistory && recent.length === 0 && (
              <div className="table-row">
                <span>No screenings yet</span>
              </div>
            )}

            {!loadingHistory && recent.map((record) => (
              <Link
                className="table-row"
                to={`/result?id=${record.id}`}
                key={record.id}
              >
                <span>{record.passportNumber || record.name || record.id}</span>
                <span>{record.documentType}</span>
                <span className={`risk ${record.risk.toLowerCase()}`}>
                  {record.risk}
                </span>
                <span>{record.score}/100</span>
                <span>{record.verified ? "✓ Verified" : "⚠ Review"}</span>
              </Link>
            ))}

          </div>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;