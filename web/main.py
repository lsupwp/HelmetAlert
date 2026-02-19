from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# Import routes
from routes import Home, ErrorResponse, Images

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=["templates", "partials"])

# Register routes (Express style)
app.include_router(Home().router)
app.include_router(Images().router)

# Register error handlers
ErrorResponse(app)