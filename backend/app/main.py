import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import AsyncSessionLocal, init_db

logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)


async def _maybe_seed() -> None:
    """Seed the database with mock properties if it appears empty."""
    try:
        from sqlalchemy import func, select

        from app.models.property import Property

        from app import seed as seed_module  # seed(db) provided by app.seed

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count()).select_from(Property))
            count = result.scalar_one()
            if count and count > 0:
                logger.info("Database already populated (%s properties); skipping seed.", count)
                return

            # app.seed.seed(db) is async and manages its own commits.
            await seed_module.seed(session)
        logger.info("Seed completed.")
    except Exception as exc:  # pragma: no cover - best-effort startup seeding
        logger.warning("Skipping DB seed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await init_db()
        logger.info("Database initialized.")
    except Exception as exc:
        logger.error("init_db failed: %s", exc)
    await _maybe_seed()
    yield
    # Shutdown (nothing to clean up explicitly)


app = FastAPI(
    title="AI-Powered Property Valuation & Lead Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


# Routers are built by another agent; include each defensively so the app
# still boots even if one module is not yet present.
def _include_routers() -> None:
    # Each router module already declares its own prefix (e.g. "/auth"), so they
    # are all mounted under the shared "/api" base — NOT "/api/auth" etc., which
    # would double the path segment (e.g. /api/auth/auth/login).
    router_specs = [
        ("app.routers.auth", "/api", ["auth"]),
        ("app.routers.properties", "/api", ["properties"]),
        ("app.routers.dashboard", "/api", ["dashboard"]),
        ("app.routers.chat", "/api", ["chat"]),
        ("app.routers.saved", "/api", ["saved"]),
    ]
    import importlib

    for module_path, prefix, tags in router_specs:
        try:
            module = importlib.import_module(module_path)
            router = getattr(module, "router")
            app.include_router(router, prefix=prefix, tags=tags)
            logger.info("Mounted router %s at %s", module_path, prefix)
        except Exception as exc:
            logger.warning("Could not mount router %s: %s", module_path, exc)


_include_routers()
