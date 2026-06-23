from app.core.utils.router import collect_routers


router = collect_routers(__name__, __path__, prefix="/tistory", tags=["tistory"])