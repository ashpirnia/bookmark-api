from fastapi import FastAPI

from app.routers import auth, bookmarks

app = FastAPI(title="Bookmarks API")

app.include_router(auth.router)
app.include_router(bookmarks.router)
