import { useState } from "react";

function Profile() {
  const [currentUser, setCurrentUser] = useState(null);
  const [mode, setMode] = useState("login");

  const handleSubmit = (event) => {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const email = formData.get("email")?.toString().trim() || "";
    const fullName = formData.get("name")?.toString().trim() || "";

    if (!email) {
      return;
    }

    const displayName =
      fullName ||
      email
        .split("@")[0]
        .replace(/[._-]+/g, " ")
        .replace(/\b\w/g, (char) => char.toUpperCase());

    setCurrentUser({
      name: displayName,
      email,
      accountType: mode === "signup" ? "New Account" : "Existing Account",
    });
  };

  const handleLogout = () => {
    setCurrentUser(null);
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card profile-summary">
        {!currentUser ? (
          <>
            <h2>{mode === "login" ? "Login" : "Create Account"}</h2>

            <div className="auth-toggle" role="tablist" aria-label="Authentication mode">
              <button
                type="button"
                className={mode === "login" ? "active" : ""}
                onClick={() => setMode("login")}
              >
                Login
              </button>
              <button
                type="button"
                className={mode === "signup" ? "active" : ""}
                onClick={() => setMode("signup")}
              >
                Sign Up
              </button>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
              {mode === "signup" && (
                <label>
                  Full Name
                  <input type="text" name="name" placeholder="Enter your full name" required />
                </label>
              )}

              <label>
                Email
                <input type="email" name="email" placeholder="Enter your email" required />
              </label>

              <label>
                Password
                <input
                  type="password"
                  name="password"
                  placeholder="Enter your password"
                  required
                />
              </label>

              {mode === "signup" && (
                <label>
                  Confirm Password
                  <input
                    type="password"
                    name="confirmPassword"
                    placeholder="Confirm your password"
                    required
                  />
                </label>
              )}

              <button type="submit" className="auth-submit">
                {mode === "login" ? "Login" : "Create Account"}
              </button>
            </form>
          </>
        ) : (
          <>
            <h2>Profile</h2>
            <p><strong>Name:</strong> {currentUser.name}</p>
            <p><strong>Email:</strong> {currentUser.email}</p>
            <p><strong>Status:</strong> Logged in ({currentUser.accountType})</p>
            <p><strong>Settings:</strong> Available</p>
            <button type="button" className="auth-submit" onClick={handleLogout}>
              Logout
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default Profile;