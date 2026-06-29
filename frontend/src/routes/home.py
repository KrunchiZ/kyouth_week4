from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/")
async def landing(request: Request):

    return request.app.state.templates.TemplateResponse(
        "landing.html",
        {
            "request": request
        }
    )