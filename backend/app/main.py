"""
FastAPI application entrypoint.
Startup: connect MongoDB → seed data → train ML models.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.utils.database import connect_to_mongo, close_mongo, get_db

from app.ml.engine import ml_engine
from app.routes import auth, products, interactions, recommendations, cart, orders, profile, chat
from app.schemas.schemas import HealthResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
APP_VERSION = "2.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== Smart Recommendation System v2.0 Starting ===")
    db = connect_to_mongo()

    # Smart seeding: Only seed if database is completely empty
    if db.products.count_documents({}) == 0:
        from app.utils.seed_data import seed_database
        seed_database(db)

    # Append expanded catalog if it's not present
    if db.products.count_documents({}) <= 100:
        import sys
        scripts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
        if scripts_path not in sys.path:
            sys.path.append(scripts_path)
        try:
            from append_seed_data import append_seed_data
            append_seed_data(db)
        except Exception as e:
            logger.error(f"Failed to append seed data: {e}")

    # Ensure demo user 'john.doe@example.com' exists for demo purposes
    demo_user = db.users.find_one({"email": "john.doe@example.com"})
    if not demo_user:
        from app.utils.auth import hash_password
        from datetime import datetime
        db.users.insert_one({
            "name": "John Doe",
            "email": "john.doe@example.com",
            "password_hash": hash_password("password123"),
            "age": 30,
            "location": "New York, NY",
            "created_at": datetime.utcnow(),
            "is_seed": True
        })
        logger.info("Demo user 'john.doe@example.com' created on startup.")

    # Train ML models using existing MongoDB data
    ml_engine.fit(db)
    logger.info("=== System Ready ===")
    # Run vectorization in the background so it doesn't block the startup (important for Render)
    from app.services.rag_service import rag_service
    import asyncio
    
    async def vectorize_in_background():
        try:
            import sys
            scripts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
            if scripts_path not in sys.path:
                sys.path.append(scripts_path)
            from vectorize_catalog import vectorize_catalog
            
            if rag_service.collection is None or getattr(rag_service.collection, "count", lambda: 0)() == 0:
                logger.info("Starting background vectorization task for ChromaDB...")
                # Run the blocking script in a separate thread
                await asyncio.to_thread(vectorize_catalog, None)
                
                # Re-load the newly created collection into the rag_service
                rag_service.collection = rag_service.chroma_client.get_collection("product_catalog")
                logger.info("Background vectorization task complete! AI Chat Assistant is now fully functional.")
        except Exception as e:
            logger.error(f"Background vectorization failed: {e}")

    asyncio.create_task(vectorize_in_background())
    
    yield
    close_mongo()
    logger.info("=== System Stopped ===")


app = FastAPI(
    title="Smart Product Recommendation System",
    description="Production recommendation engine with MongoDB, JWT auth, and hybrid ML strategy.",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
import time
from datetime import datetime
import traceback

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- {process_time * 1000:.2f}ms"
    )
    return response

def _format_error(status_code: int, message: str, request: Request, detail: any = None) -> dict:
    return {
        "error": True,
        "status_code": status_code,
        "message": message,
        "path": request.url.path,
        "timestamp": datetime.utcnow().isoformat(),
        "detail": detail
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=_format_error(exc.status_code, str(exc.detail), request)
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=_format_error(422, "Validation Error", request, exc.errors())
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content=_format_error(500, "An unexpected error occurred. Please try again later.", request)
    )

_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
if _cors_env.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if cors_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(products.router, prefix=PREFIX)
app.include_router(interactions.router, prefix=PREFIX)
app.include_router(recommendations.router, prefix=PREFIX)
app.include_router(cart.router, prefix=PREFIX)
app.include_router(orders.router, prefix=PREFIX)
app.include_router(profile.router, prefix=PREFIX)
app.include_router(chat.router, prefix=PREFIX)

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    db = get_db()
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        total_users=db.users.count_documents({}),
        total_products=db.products.count_documents({}),
        total_interactions=db.interactions.count_documents({}),
        ml_engine_ready=ml_engine.is_ready,
    )


import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount the static directory for assets (CSS, JS, images)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    # Catch-all route to serve the React index.html for all non-API routes
    @app.get("/{catchall:path}", tags=["System"])
    def serve_react_app(catchall: str):
        if catchall.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    @app.get("/", tags=["System"])
    def root():
        return {
            "message": "Smart Product Recommendation System API (Frontend not built)",
            "docs": "/docs",
        }
