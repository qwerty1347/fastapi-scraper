import importlib
import pkgutil

from fastapi import APIRouter


def collect_routers(package_name, package_path, **router_kwargs):
    """
    패키지 하위의 router 들을 모아 하나의 APIRouter 로 반환한다.

    규칙:
      - 하위 디렉토리(서브패키지)
          · 그 패키지의 __init__ 이 router 를 노출하면 그것을 사용 (집계형 디렉토리)
          · 아니면 디렉토리의 router.py 의 router 를 사용 (단일 router.py 형)
      - 같은 폴더의 router.py → 직속 라우트로 포함

    router_kwargs: APIRouter 에 그대로 전달 (prefix, tags, dependencies, responses 등)

    덕분에 각 __init__.py 는 이 함수 호출 한 줄로 끝난다.
    실제 엔드포인트는 항상 router.py 에만 정의하면 된다.
    """
    aggregate = APIRouter(**router_kwargs)

    for module in pkgutil.iter_modules(package_path):
        if module.ispkg:
            package = importlib.import_module(f"{package_name}.{module.name}")
            sub_router = getattr(package, "router", None)
            if sub_router is None:
                sub_router = _load_router(f"{package_name}.{module.name}.router")
            ref = f"{package_name}.{module.name}"
        elif module.name == "router":
            sub_router = _load_router(f"{package_name}.router")
            ref = f"{package_name}.router"
        else:
            continue

        if sub_router is not None:
            aggregate.include_router(sub_router)
        else:
            print(f"[router] {ref}: router 없음 — 건너뜀")

    return aggregate


def _load_router(module_path):
    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        return None
    return getattr(module, "router", None)