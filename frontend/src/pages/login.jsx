import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Login() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = (e) => {

    e.preventDefault();

    const savedUser = JSON.parse(
      localStorage.getItem("borderguardRegisteredUser")
    );

    if (!savedUser) {
      setError("No account found. Please register first.");
      return;
    }

    if (
      email !== savedUser.email ||
      password !== savedUser.password
    ) {
      setError("Invalid email or password.");
      return;
    }

    localStorage.setItem(
      "borderguardUser",
      JSON.stringify(savedUser)
    );

    navigate("/dashboard");
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

          <button className="primary-btn">
            Sign In
          </button>

          <div className="divider">
            <span>OR</span>
          </div>

          <button
            type="button"
            className="demo-btn"
            onClick={() => {
              setEmail("demo@borderguard.ai");
              setPassword("123456");

              
            }}
          >
            Use Demo Account
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