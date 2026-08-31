from fastapi import FastAPI  # type: ignore[import-not-found]

app = FastAPI(
    title="BorderAI",
    description="AI-assisted identity and document screening system",
    version="1.0.0"
)


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ok",
        "service": "BorderAI"
    }