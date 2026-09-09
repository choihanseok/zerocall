from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from zerocall.common.config import Settings, load_settings
from zerocall.common.database import check_database, make_engine
from zerocall.common.errors import ApplicationError
from zerocall.common.logging import get_logger


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    engine = make_engine(settings)
    logger = get_logger()

    @asynccontextmanager
    async def lifespan(_app):
        try:
            check_database(engine)
        except Exception:
            engine.dispose()
            raise RuntimeError("Database unavailable") from None
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.engine = engine

    def error_response(request, code, message, status):
        return JSONResponse(
            status_code=status,
            content={
                "success": False,
                "error": {"code": code, "message": message},
                "traceId": request.state.trace_id,
            },
        )

    @app.middleware("http")
    async def trace_request(request: Request, call_next):
        request.state.trace_id = str(uuid4())
        try:
            response = await call_next(request)
        except Exception:
            response = error_response(
                request, "INTERNAL_SERVER_ERROR", "요청을 처리하지 못했습니다.", 500
            )
        response.headers["X-Trace-ID"] = request.state.trace_id
        logger.info(
            "request",
            extra={
                "event": "http_request",
                "trace_id": request.state.trace_id,
                "environment": settings.environment,
                "status": response.status_code,
            },
        )
        return response

    @app.exception_handler(ApplicationError)
    async def application_error(request: Request, exc: ApplicationError):
        return error_response(request, exc.code, exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _exc: RequestValidationError):
        return error_response(request, "VALIDATION_FAILED", "입력값을 확인해 주세요.", 422)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        code = "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return error_response(request, code, "요청을 처리할 수 없습니다.", exc.status_code)

    @app.get("/health")
    def health(request: Request):
        try:
            check_database(engine)
        except Exception:
            return error_response(request, "DATABASE_UNAVAILABLE", "서비스 준비 중입니다.", 503)
        return {"status": "UP"}

    return app
