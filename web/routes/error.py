from .route import Routes, Request

class ErrorResponse(Routes):
    def __init__(self, app=None):
        super().__init__()
        # ถ้ามี app ให้ register exception handler
        if app:
            self.register_handlers(app)

    def error_404(self, request: Request):
        return self.render(
            request=request,
            name="error/404.html",
            context={
                "title": "404 Not Found"
            }
        )
    
    def register_handlers(self, app):
        from starlette.exceptions import HTTPException as StarletteHTTPException
        
        @app.exception_handler(StarletteHTTPException)
        async def custom_404_handler(request: Request, exc: StarletteHTTPException):
            if exc.status_code == 404:
                return self.error_404(request)
            raise exc