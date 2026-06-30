from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/chatbot")
async def chatbot(request: Request):

    return request.app.state.templates.TemplateResponse(
        request, "chatbot.html",
        {
            "request": request
        }
    )