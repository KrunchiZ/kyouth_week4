from fastapi import APIRouter, Request
from services.backend import get_cards

router = APIRouter()

@router.get("/dashboard")
async def dashboard(request: Request):

    data = await get_cards()

    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "cards": data["cards"]
        }
    )