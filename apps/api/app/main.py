from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .problems import register_exception_handlers
from .routers import categories, departments, health, subcategories, taxonomy, zones

settings = get_settings()

app = FastAPI(title="Retail Taxonomy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(zones.router)
app.include_router(departments.router)
app.include_router(categories.router)
app.include_router(subcategories.router)
app.include_router(taxonomy.router)


@app.get("/")
def root():
    return {"service": settings.service_name, "docs": "/docs", "openapi": "/openapi.json"}
