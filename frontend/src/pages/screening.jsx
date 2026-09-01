import { useState } from "react";
import { useNavigate } from "react-router-dom";

function Screening() {

  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [documentType] = useState("Passport");
  const [loading, setLoading] = useState(false);

  const handleFile = (e) => {
    const selectedFile = e.target.files[0];

    if (!selectedFile) return;

    setFile(selectedFile);
  };

  const startAnalysis = async () => {

    if (!file) {
      alert("Please upload a document first.");
      return;
    }

    // Passport-only system
    if (documentType !== "Passport") {
      alert("This system currently supports passport verification only.");
      return;
    }

    // Maximum 10 MB
    if (file.size > 10 * 1024 * 1024) {
      alert("File size must be less than 10MB.");
      return;
    }

    setLoading(true);

    const formData = new FormData();

    formData.append("file", file);
    formData.append("document_type", documentType);

    try {

      const response = await fetch(
        "http://127.0.0.1:8000/verify",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Verification failed"
        );
      }

      console.log("FastAPI Response:", data);

      // Store result temporarily
      localStorage.setItem(
        "verificationResult",
        JSON.stringify(data)
      );

      navigate("/result");

    } catch (error) {

      console.error(
        "Verification Error:",
        error
      );

      alert(
        error.message ||
        "Unable to connect to the FastAPI server."
      );

    } finally {

      setLoading(false);

    }
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
            Upload Passport
          </h2>

          <p>
            Upload a clear image of the passport
            you want to verify.
          </p>


          <label className="upload-area">

            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg"
              onChange={handleFile}
            />

            <span className="upload-cloud">
              ☁
            </span>

            <strong>
              {file
                ? file.name
                : "Drop your passport here"}
            </strong>

            <small>
              PNG or JPG • Maximum 10MB
            </small>

          </label>


          <div className="document-options">

            <label>
              Document Type
            </label>

            <strong>
              Passport
            </strong>

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
              <span>
                Extract passport information
              </span>
            </div>

            <div>
              <b>02</b>
              <strong>Document Validation</strong>
              <span>
                Check passport consistency
              </span>
            </div>

            <div>
              <b>03</b>
              <strong>Tampering Detection</strong>
              <span>
                Detect document manipulation
              </span>
            </div>

            <div>
              <b>04</b>
              <strong>Face Verification</strong>
              <span>
                Analyse passport photograph
              </span>
            </div>

            <div>
              <b>05</b>
              <strong>Risk Assessment</strong>
              <span>
                Generate final verification result
              </span>
            </div>

          </div>

        </section>

      </div>

    </div>
  );
}

export default Screening;