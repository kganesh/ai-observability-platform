import { useEffect, useState } from "react";

type Incident = {
  id: number;
  title: string;
  serviceName: string;
  status: string;
};

function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Adjust URL if your incident-service is exposed differently
    fetch("http://localhost:8081/incidents")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setIncidents)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <main style={{ padding: "1.5rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>AI Observability – Incidents</h1>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}
      {incidents.length === 0 && !error && <p>No incidents yet.</p>}

      <ul>
        {incidents.map((inc) => (
          <li key={inc.id}>
            <strong>#{inc.id}</strong> – {inc.title || "(no title)"} –{" "}
            {inc.serviceName} – <em>{inc.status}</em>
          </li>
        ))}
      </ul>
    </main>
  );
}

export default App;