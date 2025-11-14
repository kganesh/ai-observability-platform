import { useEffect, useState } from "react";

export default function App() {
  const [incidents, setIncidents] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8081/incidents")
      .then(r => r.json())
      .then(setIncidents);
  }, []);

  return (
    <div>
      <h1>Incidents</h1>
      <ul>
        {incidents.map(i => (
          <li key={i.id}>{i.serviceName} — {i.status}</li>
        ))}
      </ul>
    </div>
  );
}