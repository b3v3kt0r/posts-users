from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from comments import schemas
from database.engine import get_db
from comments.models import Comment
from posts.models import Post
from users import models, services

comments_router = APIRouter()


@comments_router.get("/comments/{post_id}", response_model=list[schemas.Comment])
def get_comments_for_post(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    if not comments:
        raise HTTPException(status_code=404, detail="Comments not found")
    return comments


@comments_router.post("/posts/{post_id}/comments", response_model=schemas.Comment)
def create_comment(
        post_id: int,
        comment: schemas.CommentCreate,
        user: models.User = Depends(services.get_current_user),
        db: Session = Depends(get_db)
):

    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    db_comment = Comment(
        content=comment.content,
        post_id=post_id,
        user_id=user.id,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment
