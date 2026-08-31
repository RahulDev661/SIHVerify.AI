import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Screening() {

  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [documentType, setDocumentType] = useState("Passport");
  const [loading, setLoading] = useState(false);

  const handleFile = (e) => {
    setFile(e.target.files[0]);
  };

  const startAnalysis = () => {

    if (!file) {
      alert("Please upload a document first.");
      return;
    }

    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      navigate("/result");
    }, 2500);
  };

  return (
    <div className="screening-page">

      <header className="page-header">

        <div>
          <span>SCREENING CENTER</span>
          <h1>New Document Screening</h1>
        </div>

        <button
          onClick={() => navigate("/dashboard")}
          className="back-btn"
        >
          ← Dashboard
        </button>

      </header>

      <div className="screening-container">

        <section className="upload-card">

          <div className="upload-icon">
            ↑
          </div>

          <h2>
            Upload Identity Document
          </h2>

          <p>
            Upload a clear image or PDF of the document
            you want to screen.
          </p>

          <label className="upload-area">

            <input
              type="file"
              accept="image/*,.pdf"
              onChange={handleFile}
            />

            <span className="upload-cloud">
              ☁
            </span>

            <strong>
              {file
                ? file.name
                : "Drop your document here"}
            </strong>

            <small>
              PNG, JPG or PDF • Maximum 10MB
            </small>

          </label>

          <div className="document-options">

            <label>
              Document Type
            </label>

            <select
              value={documentType}
              onChange={(e) =>
                setDocumentType(e.target.value)
              }
            >
              <option>Passport</option>
              <option>Visa</option>
              <option>National ID</option>
              <option>Driving License</option>
              <option>Permit</option>
            </select>

          </div>

          <button
            className="primary-btn analyze-btn"
            onClick={startAnalysis}
            disabled={loading}
          >
            {loading
              ? "AI Analysis Running..."
              : "Start AI Screening →"}
          </button>

        </section>

        <section className="pipeline-card">

          <h2>AI Screening Pipeline</h2>

          <div className="pipeline">

            <div>
              <b>01</b>
              <strong>OCR Extraction</strong>
              <span>Extract identity information</span>
            </div>

            <div>
              <b>02</b>
              <strong>Document Validation</strong>
              <span>Check document consistency</span>
            </div>

            <div>
              <b>03</b>
              <strong>Tampering Detection</strong>
              <span>Detect manipulation signals</span>
            </div>

            <div>
              <b>04</b>
              <strong>Face Verification</strong>
              <span>Compare identity faces</span>
            </div>

            <div>
              <b>05</b>
              <strong>Risk Assessment</strong>
              <span>Generate final risk score</span>
            </div>

          </div>

        </section>

      </div>

    </div>
  );
}

export default Screening;