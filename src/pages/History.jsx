import { Link } from "react-router-dom";

function History() {

  const records = [
    {
      id: "A7821346",
      type: "Passport",
      score: 86,
      risk: "HIGH"
    },
    {
      id: "V9211002",
      type: "Visa",
      score: 48,
      risk: "MEDIUM"
    },
    {
      id: "ID8812009",
      type: "National ID",
      score: 18,
      risk: "LOW"
    },
    {
      id: "DL5566778",
      type: "Driving License",
      score: 12,
      risk: "LOW"
    }
  ];

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

      <div className="history-table">

        {records.map((record) => (

          <div className="history-row" key={record.id}>

            <div>
              <strong>{record.id}</strong>
              <span>{record.type}</span>
            </div>

            <span className={`risk ${record.risk.toLowerCase()}`}>
              {record.risk}
            </span>

            <strong>
              {record.score}/100
            </strong>

            <Link to="/result">
              View →
            </Link>

          </div>

        ))}

      </div>

    </div>
  );
}

export default History;