from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@router.get("/recipes", response_class=HTMLResponse)
def recipes_list(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "recipes.html")


@router.get("/recipes/new", response_class=HTMLResponse)
def recipe_new(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "recipe_form.html", {"recipe_id": None})


@router.get("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
def recipe_edit(request: Request, recipe_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "recipe_form.html", {"recipe_id": recipe_id}
    )
