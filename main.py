from fastapi import FastAPI
from database.connection import Base, engine
from api.tables import router as table_router
from api.reservations import router as reservation_router
from errors.handlers import register_error_handlers

app = FastAPI(
    title="Table Reservation System API",
    description="Clean, modular FastAPI enterprise blueprint with structured architecture.",
    version="2.0.0"
)

# Set up local database tables (Runs automatically in development)
Base.metadata.create_all(bind=engine)

# Register custom global exceptions so APIs return standard errors nicely
register_error_handlers(app)

# Include API routers under global /api namespace
app.include_router(table_router, prefix="/api")
app.include_router(reservation_router, prefix="/api")

@app.get("/", tags=["Health Diagnostics"])
def health_check():
    return {
        "status": "online",
        "system": "Table Reservation API",
        "documentation": "/docs"
    }