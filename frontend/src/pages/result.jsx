import { useNavigate } from "react-router-dom";

function Result() {

  const navigate = useNavigate();

  return (
    <div className="result-page">

      <header className="page-header">

        <div>
          <span>SCREENING REPORT</span>
          <h1>Analysis Result</h1>
        </div>

        <button
          className="back-btn"
          onClick={() => navigate("/dashboard")}
        >
          ← Dashboard
        </button>

      </header>

      {/* Risk Banner */}

      <section className="risk-banner">

        <div>

          <span>FINAL RISK ASSESSMENT</span>

          <h2>
            High Risk Detected
          </h2>

          <p>
            Manual verification is recommended
            before accepting this document.
          </p>

        </div>

        <div className="risk-score">
          <strong>86</strong>
          <span>/100</span>
        </div>

      </section>

      {/* Document Info */}

      <section className="result-grid">

        <div className="result-card">

          <h2>Extracted Information</h2>

          <div className="info-row">
            <span>Name</span>
            <strong>Rahul Kumar</strong>
          </div>

          <div className="info-row">
            <span>Passport Number</span>
            <strong>A7821346</strong>
          </div>

          <div className="info-row">
            <span>Nationality</span>
            <strong>Indian</strong>
          </div>

          <div className="info-row">
            <span>Date of Birth</span>
            <strong>12/05/1995</strong>
          </div>

          <div className="info-row">
            <span>Expiry Date</span>
            <strong>11/05/2030</strong>
          </div>

        </div>

        {/* AI modules */}

        <div className="result-card">

          <h2>AI Analysis</h2>

          <div className="analysis-item">
            <div>
              <strong>OCR Extraction</strong>
              <span>Information extracted</span>
            </div>
            <b className="status-good">✓ PASS</b>
          </div>

          <div className="analysis-item">
            <div>
              <strong>Document Validation</strong>
              <span>Inconsistency detected</span>
            </div>
            <b className="status-warning">⚠ REVIEW</b>
          </div>

          <div className="analysis-item">
            <div>
              <strong>Tampering Detection</strong>
              <span>Manipulation suspected</span>
            </div>
            <b className="status-danger">✕ HIGH</b>
          </div>

          <div className="analysis-item">
            <div>
              <strong>Face Verification</strong>
              <span>Face mismatch</span>
            </div>
            <b className="status-danger">✕ FAIL</b>
          </div>

        </div>

      </section>

      {/* Findings */}

      <section className="findings-card">

        <h2>Security Findings</h2>

        <div className="finding danger-finding">
          <span>01</span>
          <div>
            <strong>Text Manipulation Suspected</strong>
            <p>
              Anomaly detected around the date of birth region.
            </p>
          </div>
        </div>

        <div className="finding warning-finding">
          <span>02</span>
          <div>
            <strong>Metadata Inconsistency</strong>
            <p>
              Image metadata does not match expected values.
            </p>
          </div>
        </div>

        <div className="finding danger-finding">
          <span>03</span>
          <div>
            <strong>Face Mismatch</strong>
            <p>
              Document face and presented face similarity is
              below the verification threshold.
            </p>
          </div>
        </div>

        <div className="finding good-finding">
          <span>04</span>
          <div>
            <strong>No Stamp Forgery Signal</strong>
            <p>
              No significant anomaly detected in the stamp region.
            </p>
          </div>
        </div>

      </section>

      {/* Audit */}

      <section className="audit-card">

        <div>
          <span>SECURITY AUDIT</span>
          <h2>Screening Audit Record</h2>
        </div>

        <div className="hash">
          <small>DOCUMENT HASH</small>
          <code>
            8a92f72c4be8e2c91ab...
          </code>
        </div>

        <div className="audit-status">
          ✓ Audit record generated
        </div>

      </section>

    </div>
  );
}

export default Result;