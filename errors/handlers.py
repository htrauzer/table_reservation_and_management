from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# Custom Base Exception
class RestaurantException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.detail = message  # Solution 2: Added detail attribute
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


def register_error_handlers(app: FastAPI):
    """Registers global custom handlers to catch and format API domain errors elegantly."""
    @app.exception_handler(RestaurantException)
    async def restaurant_exception_handler(request: Request, exc: RestaurantException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": exc.message}
        )