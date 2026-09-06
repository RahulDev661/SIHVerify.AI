import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory } from "../api";

function History() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getHistory()
      .then(setRecords)
      .catch((err) => setError(err.message || "Could not load history"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="simple-page">

      <div className="page-header">

        <div>
          <span>RECORDS</span>
          <h1>Screening History</h1>
        </div>

        <Link
          to="/dashboard"
          className="back-btn"
        >
          ← Dashboard
        </Link>

      </div>

      {loading && <p>Loading history…</p>}

      {!loading && error && <p className="finding danger-finding">{error}</p>}

      {!loading && !error && records.length === 0 && (
        <p>No screenings yet. Run one from "New Screening" to see it here.</p>
      )}

      {!loading && !error && records.length > 0 && (
        <div className="history-table">

          {records.map((record) => (

            <div className="history-row" key={record.id}>

              <div>
                <strong>{record.passportNumber || record.name || record.id}</strong>
                <span>{record.documentType}</span>
              </div>

              <span className={`risk ${record.risk.toLowerCase()}`}>
                {record.risk}
              </span>

              <strong>
                {record.score}/100
              </strong>

              <Link to={`/result?id=${record.id}`}>
                View →
              </Link>

            </div>

          ))}

        </div>
      )}

    </div>
  );
}

export default History;
