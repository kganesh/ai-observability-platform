from fastapi import FastAPI
import psycopg2
import google.generativeai as genai
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.0-pro')

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

    resp = model.generate_content(prompt)

    rca = resp.text

    cur.execute("UPDATE incidents SET rca_text=%s WHERE id=%s", (rca, incident_id))
    PG.commit()

    return {"rca": rca}