# python -m uvicorn main:app --reload
import hashlib
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound


from api import data_url   

from api import data_url, coord  

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("main")

app = FastAPI()

TEMPLATES_DIR = "templates"
STATIC_DIR = "static"
IMGS_DIR = "imgs"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/imgs", StaticFiles(directory=IMGS_DIR), name="imgs")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

def _safe_imgs_path(filename: str) -> str:
    if ".." in filename or filename.startswith("/") or "\\" in filename:
        raise HTTPException(status_code=400, detail="Некорректное имя файла")
    return os.path.join(IMGS_DIR, filename)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    try:
        return templates.TemplateResponse("main.html", {"request": request})
    except TemplateNotFound:
        return HTMLResponse("<h1>Главная страница не найдена</h1>", status_code=200)

@app.get("/weather/{region_id}")
async def get_weather(region_id: str):
    region_id = region_id.strip().lower()
    if region_id not in coord:
        return JSONResponse(status_code=404, content={"error": "Регион не найден"})
    try:
        data = data_url(region_id)
        return JSONResponse(content=data)
    except Exception as e:
        logger.exception("Ошибка при получении погоды для %s", region_id)
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/{city}", response_class=HTMLResponse)
async def city_page(request: Request, city: str):
    city = city.strip().lower()
    candidates = [f"{city}.html", f"{city}.htm"]
    for tmpl in candidates:
        try:
            return templates.TemplateResponse(tmpl, {"request": request})
        except TemplateNotFound:
            continue
    return templates.TemplateResponse("main.html", {"request": request})

@app.get("/images/{filename}")
async def image_file(filename: str):
    path = _safe_imgs_path(filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(path)

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    logger.info("Запускаем app на %s:%s", host, port)
    uvicorn.run("main:app", host=host, port=port, reload=True)



