from .route import Routes, Request

class Home(Routes):
    def __init__(self):
        super().__init__()
        # Register routes (ไม่ต้องใส่ response_class แล้ว สืบทอดจาก Routes)
        self.router.add_api_route("/", self.home, methods=["GET"])
        self.router.add_api_route("/dashbord", self.dashbord, methods=["GET"])

    def home(self, request: Request):
        return self.render(
            request=request,
            name="home.html",
            context={
                "title": "Home"
            }
        )

    def dashbord(self, request: Request):
        return self.render(
            request=request,
            name="dashbord.html",
            context={
                "title": "dashbord"
            }
        )