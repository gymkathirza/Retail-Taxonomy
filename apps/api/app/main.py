from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.problem import http_exception_handler, validation_exception_handler
from app.routers import categories, departments, health, subcategories, taxonomy, zones

app = FastAPI(title="Retail Taxonomy API", version="0.1.0")
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(health.router)
app.include_router(zones.router)
app.include_router(departments.nested)
app.include_router(departments.router)
app.include_router(categories.nested)
app.include_router(categories.router)
app.include_router(subcategories.nested)
app.include_router(subcategories.router)
app.include_router(taxonomy.router)
