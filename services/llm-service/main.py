from fastapi import FastAPI
import psycopg2
import requests
import openai

app = FastAPI()

PG = psycopg2.connect(host="postgres", dbname="observability",
                      user="admin", password="admin")

@app.post("/explain-incident/{incident_id}")
def explain(incident_id: int):
    cur = PG.cursor()
    cur.execute("SELECT * FROM incidents WHERE id=%s", (incident_id,))
    incident = cur.fetchone()

    prompt = f"""
    Incident details:
    ID: {incident_id}
    Data: {incident}

    Explain probable root cause and suggested actions.
    """

    resp = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": "You are an SRE assistant."},
                  {"role": "user", "content": prompt}]
    )

    rca = resp['choices'][0]['message']['content']

    cur.execute("UPDATE incidents SET rca_text=%s WHERE id=%s", (rca, incident_id))
    PG.commit()

    return {"rca": rca}