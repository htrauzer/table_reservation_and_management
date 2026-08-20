import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from database.connection import Base, engine, SessionLocal
from database.models import TableModel
from api.tables import router as table_router
from api.reservations import router as reservation_router
from errors.handlers import register_error_handlers


# 1. Modern Lifespan Manager for Startup / Seeding
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    
    # Database seeding logic
    db = SessionLocal()
    try:
        if db.query(TableModel).count() == 0:
            print("Database has no tables. Seeding physical layout configurations...")
            default_tables = [
                # Private Area Left (A)
                TableModel(table_number="T1", capacity=2, zone="private-a"),
                TableModel(table_number="T2", capacity=4, zone="private-a"),
                
                # Main Hall (Center)
                TableModel(table_number="T3", capacity=4, zone="main-hall"),
                TableModel(table_number="T4", capacity=6, zone="main-hall"),
                TableModel(table_number="T5", capacity=2, zone="main-hall", is_active=False),  # Out of service
                TableModel(table_number="T6", capacity=8, zone="main-hall"),
                
                # Private Area Right (B)
                TableModel(table_number="T7", capacity=2, zone="private-b"),
                TableModel(table_number="T8", capacity=4, zone="private-b"),
                
                # Terrace (Bottom)
                TableModel(table_number="T9", capacity=2, zone="terrace"),
                TableModel(table_number="T10", capacity=4, zone="terrace"),
                TableModel(table_number="T11", capacity=6, zone="terrace")
            ]
            db.bulk_save_objects(default_tables)
            db.commit()
            print("Successfully seeded database tables!")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()
        
    yield  # Application runs here


# 2. Application Definition
app = FastAPI(
    title="Table Reservation System API",
    description="Clean, modular FastAPI enterprise blueprint with structured architecture.",
    version="2.0.0",
    lifespan=lifespan
)

# 3. CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Mount Static Assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# 5. Exception Handlers
register_error_handlers(app)

# 6. Routers
app.include_router(table_router, prefix="/api")
app.include_router(reservation_router, prefix="/api")


# 7. Health Check Endpoint for Playwright webServer Readiness
@app.get("/health", status_code=status.HTTP_200_OK, tags=["System Health"])
def health_check():
    """Endpoint used by automated test runners to verify server boot status."""
    return {"status": "ok"}


# 8. Main Index HTML Route
@app.get("/", response_class=HTMLResponse, tags=["Frontend UI Template"])
def serve_homepage():
    """Serves the interactive restaurant map home page from templates/index.html"""
    html_path = os.path.join("templates", "index.html")
    if not os.path.exists(html_path):
        return HTMLResponse(
            status_code=404,
            content="<h1>404 File Not Found</h1><p>Please place index.html in your templates folder.</p>"
        )
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())