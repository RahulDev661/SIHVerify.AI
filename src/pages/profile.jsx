import { Link } from "react-router-dom";

function Profile() {

  const user = JSON.parse(
    localStorage.getItem("borderguardUser")
  );

  return (
    <div className="simple-page">

      <div className="page-header">

        <div>
          <span>ACCOUNT</span>
          <h1>Officer Profile</h1>
        </div>

        <Link
          to="/dashboard"
          className="back-btn"
        >
          ← Dashboard
        </Link>

      </div>

      <div className="profile-card">

        <div className="profile-avatar">
          {user?.name?.charAt(0)}
        </div>

        <h2>{user?.name}</h2>

        <p>Security Screening Officer</p>

        <div className="profile-info">

          <div>
            <span>Email</span>
            <strong>{user?.email}</strong>
          </div>

          <div>
            <span>Officer ID</span>
            <strong>{user?.officerId}</strong>
          </div>

          <div>
            <span>System Role</span>
            <strong>Screening Officer</strong>
          </div>

        </div>

      </div>

    </div>
  );
}

export default Profile;