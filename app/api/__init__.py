from app.core.utils.router import collect_routers


api_router = collect_routers(__name__, __path__, prefix="/api")