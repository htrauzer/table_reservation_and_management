import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("uvicorn.error")

# ==========================================
# 1. CUSTOM DOMAIN EXCEPTIONS
# ==========================================

class RestaurantException(Exception):
    """Base domain exception for restaurant management operations."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.detail = message
        self.status_code = status_code
        super().__init__(self.message)


class TableConflictException(RestaurantException):
    def __init__(self, message: str = "This table is already booked for the selected time slot."):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class TableNotFoundException(RestaurantException):
    def __init__(self, message: str = "The requested table does not exist."):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class TableCapacityException(RestaurantException):
    def __init__(self, message: str = "The table doesn't have enough capacity for this party size."):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 2. HANDLER REGISTRATION
# ==========================================

def register_error_handlers(app: FastAPI):
    """Registers global custom handlers to catch and format API domain errors elegantly."""
    
    @app.exception_handler(RestaurantException)
    async def restaurant_exception_handler(request: Request, exc: RestaurantException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.message,
                "detail": exc.message  # Added for compatibility with standard FastAPI consumers
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Extracts readable validation errors (e.g. invalid phone/email)
        errors = [f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()]
        error_msg = "; ".join(errors)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation Error",
                "detail": error_msg
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server exception on {request.url}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal Server Error",
                "detail": "An unexpected server error occurred."
            }
        )