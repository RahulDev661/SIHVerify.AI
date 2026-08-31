import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Register() {

  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    email: "",
    officerId: "",
    password: "",
    confirmPassword: ""
  });

  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  const handleRegister = (e) => {
    e.preventDefault();

    setError("");

    if (
      !form.name ||
      !form.email ||
      !form.officerId ||
      !form.password ||
      !form.confirmPassword
    ) {
      setError("Please fill all fields.");
      return;
    }

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (form.password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }

    const user = {
      name: form.name,
      email: form.email,
      officerId: form.officerId,
      password: form.password
    };

    localStorage.setItem(
      "borderguardRegisteredUser",
      JSON.stringify(user)
    );

    navigate("/login");
  };

  return (
    <div className="auth-container">

      <div className="auth-left">
        <div className="brand">
          <div className="brand-icon">🛡️</div>

          <div>
            <h2>BorderGuard AI</h2>
            <p>Intelligent Document Screening</p>
          </div>
        </div>

        <div className="auth-content">
          <h1>Secure Identity.</h1>
          <h1>Smarter Screening.</h1>

          <p>
            AI-powered document verification for faster,
            safer and more reliable identity screening.
          </p>

          <div className="security-points">
            <span>✓ OCR Document Extraction</span>
            <span>✓ Tampering Detection</span>
            <span>✓ Face Verification</span>
            <span>✓ Risk Assessment</span>
          </div>
        </div>
      </div>

      <div className="auth-right">

        <form className="auth-card" onSubmit={handleRegister}>

          <div className="auth-heading">
            <h1>Create Account</h1>
            <p>Register as a screening officer</p>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <label>Full Name</label>

          <input
            type="text"
            name="name"
            placeholder="Enter your full name"
            value={form.name}
            onChange={handleChange}
          />

          <label>Email Address</label>

          <input
            type="email"
            name="email"
            placeholder="officer@example.com"
            value={form.email}
            onChange={handleChange}
          />

          <label>Officer ID</label>

          <input
            type="text"
            name="officerId"
            placeholder="Enter officer ID"
            value={form.officerId}
            onChange={handleChange}
          />

          <label>Password</label>

          <input
            type="password"
            name="password"
            placeholder="Create password"
            value={form.password}
            onChange={handleChange}
          />

          <label>Confirm Password</label>

          <input
            type="password"
            name="confirmPassword"
            placeholder="Confirm password"
            value={form.confirmPassword}
            onChange={handleChange}
          />

          <button className="primary-btn">
            Create Account
          </button>

          <p className="auth-footer">
            Already have an account?
            <Link to="/login"> Login</Link>
          </p>

        </form>

      </div>

    </div>
  );
}

export default Register;