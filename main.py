from fastapi import FastAPI

from comments.routers import comments_router
from posts.routers import posts_router
from users.routers import users_router

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(posts_router)
app.include_router(users_router)
app.include_router(comments_router)
