import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routes import router

app = FastAPI(title="Job Search Agent")
app.include_router(router)
app.mount("/static", StaticFiles(directory="dashboard"), name="static")


@app.get("/")
async def serve_dashboard():
    return FileResponse("dashboard/index.html")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)t