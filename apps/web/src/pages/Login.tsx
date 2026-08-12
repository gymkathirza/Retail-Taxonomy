import { FormEvent, useState } from "react";
import { setStoredAuth } from "../api/client";

type Props = {
  onLoggedIn: () => void;
};

export default function Login({ onLoggedIn }: Props) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("password");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setStoredAuth(username, password);
    try {
      const token = btoa(`${username}:${password}`);
      const res = await fetch("/api/v1/zones", {
        headers: { Authorization: `Basic ${token}` },
      });
      if (!res.ok) {
        throw new Error("Invalid username or password");
      }
      onLoggedIn();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="login-head">
          <div className="brand-logo">RT</div>
          <h1>Retail Taxonomy Console</h1>
          <p>Sign in with demo credentials (assessment only).</p>
        </div>
        <form className="login-body" onSubmit={onSubmit}>
          <label className="field">
            <span>Username</span>
            <input
              name="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error ? (
            <p className="login-error" role="alert">
              {error}
            </p>
          ) : null}
          <button type="submit" className="btn btn-primary">
            Sign in
          </button>
        </form>
      </div>
    </div>
  );
}
