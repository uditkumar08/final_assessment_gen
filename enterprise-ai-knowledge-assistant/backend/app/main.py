
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from backend.app.api.documents import router as documents_router
from backend.app.api.chat import router as chat_router


app = FastAPI()

app.include_router(
    documents_router,
    tags=["Document Upload"]
)

Instrumentator().instrument(app).expose(
    app,
    endpoint="/metrics"
)

app.include_router(
    chat_router,
    tags=["AI Chat"]
)


@app.get("/")
def home():

    return {
        "application": "Enterprise AI Knowledge Assistant",
        "status": "running"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }
