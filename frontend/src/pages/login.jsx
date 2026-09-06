import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { loginUser } from "../api";

function Login() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {

    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await loginUser(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Invalid email or password.");
    } finally {
      setLoading(false);
    }
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

          <div className="login-badge">
            ● SYSTEM SECURE
          </div>

          <h1>Welcome Back,</h1>
          <h1>Officer.</h1>

          <p>
            Access the intelligent identity and document
            screening platform.
          </p>

        </div>

      </div>

      <div className="auth-right">

        <form className="auth-card" onSubmit={handleLogin}>

          <div className="auth-heading">

            <h1>Officer Login</h1>

            <p>
              Sign in to continue to BorderGuard AI
            </p>

          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <label>Email Address</label>

          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <label>Password</label>

          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <div className="login-options">

            <label className="remember">
              <input type="checkbox" />
              Remember me
            </label>

            <span>Forgot password?</span>

          </div>

          <button className="primary-btn" disabled={loading}>
            {loading ? "Signing In..." : "Sign In"}
          </button>

          <p className="auth-footer">
            Don't have an account?
            <Link to="/register"> Create Account</Link>
          </p>

        </form>

      </div>

    </div>
  );
}

export default Login;