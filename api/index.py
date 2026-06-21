from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data at startup
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'q-vercel-latency.json')
with open(DATA_PATH) as f:
    DATA = json.load(f)

def percentile(arr, p):
    s = sorted(arr)
    r = (len(s) - 1) * p
    n = int(r)
    f = r - n
    if n + 1 < len(s):
        return s[n] + f * (s[n+1] - s[n])
    return s[n]

@app.post("/")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = []
    for region in regions:
        records = [d for d in DATA if d["region"] == region]
        latencies = [d["latency_ms"] for d in records]
        uptimes = [d["uptime_pct"] for d in records]

        result.append({
            "region": region,
            "avg_latency": round(sum(latencies)/len(latencies), 2),
            "p95_latency": round(percentile(latencies, 0.95), 2),
            "avg_uptime": round(sum(uptimes)/len(uptimes), 3),
            "breaches": sum(1 for l in latencies if l > threshold)
        })

    return {"regions": result}
