import { useEffect, useState } from "react";

interface Incident {
  id: number;
  serviceName: string;
  status: string;
}

export default function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);

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