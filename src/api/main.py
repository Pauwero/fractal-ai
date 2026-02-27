"""Fractal AI — FastAPI Application Entry Point.

Start with:
    uvicorn src.api.main:app --reload
"""

from fastapi import FastAPI

app = FastAPI(
    title="Fractal AI",
    description="Systematic forex trading platform — API layer",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint.

    Returns:
        Status dict confirming the API is running.
    """
    return {"status": "ok", "version": "0.1.0"}
