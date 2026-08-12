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
    <main style={{ fontFamily: "system-ui", margin: "2rem auto", maxWidth: 420 }}>
      <h1>Retail Taxonomy</h1>
      <p>Sign in with demo credentials (assessment only).</p>
      <form onSubmit={onSubmit}>
        <label>
          Username{" "}
          <input
            name="username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <br />
        <label>
          Password{" "}
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <br />
        {error ? <p role="alert">{error}</p> : null}
        <button type="submit" style={{ marginTop: "0.75rem" }}>
          Sign in
        </button>
      </form>
    </main>
  );
}
