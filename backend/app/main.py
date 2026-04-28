from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.app.models.database import init_db
from backend.app.core.logger import log_manager
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.gateway import router as gateway_router
from backend.app.api.services import router as services_router
from backend.app.api.tools import router as tools_router
from backend.app.api.chat import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await log_manager.log("AI MCP Gateway 系统启动中...", "INFO")
    yield

app = FastAPI(title="AI MCP Gateway", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(gateway_router)
app.include_router(services_router)
app.include_router(tools_router)
app.include_router(chat_router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
