import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getHistoryDetail } from "../api";

// Turns the real backend response into a 0-100 score.
// This is a simple, transparent heuristic over the actual signals
// the backend returns — it is not a fabricated AI risk model.
function computeScore(data) {
  let score = 100;
  const notes = [];

  const mrzValid = data.ocr?.structureValidation?.valid;
  if (!mrzValid) {
    score -= 40;
    notes.push({
      level: "danger",
      title: "MRZ Structure Invalid",
      detail:
        (data.ocr?.structureValidation?.errors || []).join(" ") ||
        "The machine-readable zone failed structural validation.",
    });
  }

  if (data.documentValidation && !data.documentValidation.valid) {
    score -= 30;
    notes.push({
      level: "danger",
      title: "Document Validation Failed",
      detail:
        (data.documentValidation.errors || []).join(" ") ||
        "The document did not pass validation checks.",
    });
  } else if (
    data.documentValidation &&
    data.documentValidation.confidence === 0
  ) {
    notes.push({
      level: "warning",
      title: "Document Validation Not Yet Implemented",
      detail:
        "This backend module is still a stub, so its result should not be treated as a real signal.",
    });
  }

  if (data.faceMatch) {
    if (!data.faceMatch.matched) {
      score -= 30;
      notes.push({
        level: "danger",
        title: "Face Mismatch",
        detail: `Similarity ${data.faceMatch.similarity.toFixed(
          3
        )} is below the required threshold of ${data.faceMatch.threshold}.`,
      });
    } else {
      notes.push({
        level: "good",
        title: "Face Match Confirmed",
        detail: `Similarity ${data.faceMatch.similarity.toFixed(
          3
        )} met the required threshold of ${data.faceMatch.threshold}.`,
      });
    }
  } else {
    notes.push({
      level: "warning",
      title: "Face Verification Skipped",
      detail: "No selfie was provided, so face match was not performed.",
    });
  }

  score = Math.max(0, Math.min(100, score));
  return { score, notes };
}

function riskLabel(score) {
  if (score >= 80) return { label: "Low Risk", tone: "good" };
  if (score >= 50) return { label: "Medium Risk", tone: "warning" };
  return { label: "High Risk Detected", tone: "danger" };
}

function StatusBadge({ ok, skipped }) {
  if (skipped) return <b className="status-warning">— SKIPPED</b>;
  return ok ? (
    <b className="status-good">✓ PASS</b>
  ) : (
    <b className="status-danger">✕ FAIL</b>
  );
}

function Result() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const historyId = searchParams.get("id");

  const [data, setData] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(!!historyId);

  useEffect(() => {
    if (historyId) {
      // Opened from history — fetch the stored result from the database.
      getHistoryDetail(historyId)
        .then((record) => setData(record.result))
        .catch(() => setNotFound(true))
        .finally(() => setLoading(false));
      return;
    }

    // Otherwise, this is the result of a screening just run in this
    // session — read it back from localStorage.
    const raw = localStorage.getItem("verificationResult");
    if (!raw) {
      setNotFound(true);
      return;
    }
    try {
      setData(JSON.parse(raw));
    } catch {
      setNotFound(true);
    }
  }, [historyId]);

  if (loading) {
    return (
      <div className="result-page">
        <p>Loading result…</p>
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="result-page">
        <header className="page-header">
          <div>
            <span>SCREENING REPORT</span>
            <h1>No Result Available</h1>
          </div>
        </header>
        <p>
          There's no verification result to show yet. Run a screening
          first.
        </p>
        <button
          className="primary-btn"
          onClick={() => navigate("/screening")}
        >
          Go to Screening →
        </button>
      </div>
    );
  }

  if (!data) return null;

  const { score, notes } = computeScore(data);
  const risk = riskLabel(score);
  const ocr = data.ocr || {};
  const mrzValid = ocr.structureValidation?.valid;
  const docValidation = data.documentValidation;
  const faceMatch = data.faceMatch;

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
            {data.verified ? "Verified" : risk.label}
          </h2>

          <p>
            {data.verified
              ? "This document passed all available checks."
              : "Manual verification is recommended before accepting this document."}
          </p>

        </div>

        <div className="risk-score">
          <strong>{score}</strong>
          <span>/100</span>
        </div>

      </section>

      {/* Document Info */}

      <section className="result-grid">

        <div className="result-card">

          <h2>Extracted Information</h2>

          <div className="info-row">
            <span>Name</span>
            <strong>{ocr.givenNames || ocr.surname
              ? `${ocr.givenNames || ""} ${ocr.surname || ""}`.trim()
              : "—"}</strong>
          </div>

          <div className="info-row">
            <span>Passport Number</span>
            <strong>{ocr.passportNumber || "—"}</strong>
          </div>

          <div className="info-row">
            <span>Nationality</span>
            <strong>{ocr.nationality || "—"}</strong>
          </div>

          <div className="info-row">
            <span>Date of Birth</span>
            <strong>{ocr.dob || "—"}</strong>
          </div>

          <div className="info-row">
            <span>Expiry Date</span>
            <strong>{ocr.expiry || "—"}</strong>
          </div>

        </div>

        {/* AI modules */}

        <div className="result-card">

          <h2>AI Analysis</h2>

          <div className="analysis-item">
            <div>
              <strong>OCR Extraction</strong>
              <span>{ocr.passportNumber ? "Information extracted" : "Extraction incomplete"}</span>
            </div>
            <StatusBadge ok={!!ocr.passportNumber} />
          </div>

          <div className="analysis-item">
            <div>
              <strong>MRZ Structure Validation</strong>
              <span>{mrzValid ? "Structure valid" : "Structure invalid"}</span>
            </div>
            <StatusBadge ok={mrzValid} />
          </div>

          <div className="analysis-item">
            <div>
              <strong>Document Validation</strong>
              <span>
                {docValidation
                  ? docValidation.confidence === 0
                    ? "Module not yet implemented"
                    : docValidation.documentType || "Checked"
                  : "Not run"}
              </span>
            </div>
            <StatusBadge
              ok={docValidation?.valid}
              skipped={!docValidation}
            />
          </div>

          <div className="analysis-item">
            <div>
              <strong>Face Verification</strong>
              <span>
                {faceMatch
                  ? `Similarity ${faceMatch.similarity.toFixed(3)}`
                  : "No selfie provided"}
              </span>
            </div>
            <StatusBadge ok={faceMatch?.matched} skipped={!faceMatch} />
          </div>

        </div>

      </section>

      {/* Findings */}

      <section className="findings-card">

        <h2>Security Findings</h2>

        {notes.length === 0 && (
          <div className="finding good-finding">
            <span>01</span>
            <div>
              <strong>No Issues Found</strong>
              <p>All available checks passed.</p>
            </div>
          </div>
        )}

        {notes.map((note, i) => (
          <div
            key={i}
            className={`finding ${note.level}-finding`}
          >
            <span>{String(i + 1).padStart(2, "0")}</span>
            <div>
              <strong>{note.title}</strong>
              <p>{note.detail}</p>
            </div>
          </div>
        ))}

      </section>

    </div>
  );
}

export default Result;
