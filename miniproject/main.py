from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from database import Base, engine
from router import router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="API Quản lý sinh viên theo lớp học",
    version="1.0.0"
)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "statusCode": exc.status_code,
            "message": exc.detail,
            "data": None,
            "error": exc.detail,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "path": request.url.path
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "statusCode": 422,
            "message": "Dữ liệu không hợp lệ",
            "data": None,
            "error": exc.errors(),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    return JSONResponse(
        status_code=500,
        content={
            "statusCode": 500,
            "message": "Đã xảy ra lỗi hệ thống",
            "data": None,
            "error": str(exc),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "path": request.url.path
        }
    )


app.include_router(router)


@app.get("/")
def root():
    return {
        "statusCode": 200,
        "message": "API quản lý sinh viên đang hoạt động",
        "data": None,
        "error": None,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "path": "/"
    }