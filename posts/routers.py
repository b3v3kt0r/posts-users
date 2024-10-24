from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.engine import get_db
from posts import schemas, crud
from users import services, models

posts_router = APIRouter()


@posts_router.get("/posts/", response_model=List[schemas.Post])
def get_posts(db: Session = Depends(get_db)):
    return crud.get_all_posts(db)


@posts_router.post("/posts/", response_model=schemas.Post)
def create_post(
        post: schemas.PostCreate,
        user: models.User = Depends(services.get_current_user),
        db: Session = Depends(get_db)):
    return crud.create_post(db=db, post=post, user_id=user.id)
