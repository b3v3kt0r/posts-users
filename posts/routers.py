from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.engine import get_db
from posts import schemas, crud
from posts.crud import delete_post_from_db
from users import services, models

posts_router = APIRouter()


@posts_router.get("/posts/", response_model=List[schemas.Post])
def get_posts(db: Session = Depends(get_db)):
    return crud.get_all_posts(db)


@posts_router.get("/posts/{post_id}", response_model=schemas.Post)
def get_post(post_id: int, db: Session = Depends(get_db)):
    db_post = crud.get_post_by_id(db, post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post


@posts_router.post("/posts/", response_model=schemas.Post)
def create_post(
        post: schemas.PostCreate,
        user: models.User = Depends(services.get_current_user),
        db: Session = Depends(get_db)):
    return crud.create_post(db=db, post=post, user_id=user.id)


@posts_router.delete("/posts/{post_id}", response_model=schemas.Post)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = crud.get_post_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    delete_post_from_db(db=db, post_id=post_id)
