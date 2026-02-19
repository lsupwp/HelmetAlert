from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

# Export Request เพื่อให้ไฟล์อื่นใช้ได้โดยไม่ต้อง import จาก fastapi
__all__ = ['Routes', 'Request', 'APIRouter']

class Routes:
    def __init__(self):
        # ตั้งค่า default response_class เป็น HTMLResponse
        self.router = APIRouter(default_response_class=HTMLResponse)
        self.templates = Jinja2Templates(directory=["templates", "partials"])

    def render(self, request: Request, name: str, context: dict):
        return self.templates.TemplateResponse(
            request=request,
            name=name,
            context=context
        )