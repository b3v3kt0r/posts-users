from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from comments import schemas
from comments.crud import delete_comment_from_db, update_comment_in_db, check_for_toxicity, comments_analysis, \
    auto_replay_for_comments
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

    toxicity = check_for_toxicity(comment.content)

    db_comment = Comment(
        content=comment.content,
        post_id=post_id,
        user_id=user.id,
        is_blocked=toxicity
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    if post.auto_replay_enabled:
        auto_replay_for_comments(db, comment.content, post_id, post.auto_replay_delay, post.user_id)

    return db_comment


@comments_router.put("/comments/{comment_id}", response_model=schemas.Comment)
def update_comment(
        comment_id: int,
        comment_data: schemas.Comment,
        user: models.User = Depends(services.get_current_user),
        db: Session = Depends(get_db)
):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to edit this comment")

    toxicity = check_for_toxicity(comment_data.content)
    if toxicity:
        comment.is_blocked = toxicity

    return update_comment_in_db(db=db, comment_data=comment_data, comment=comment)


@comments_router.delete("/comments/{comment_id}", response_model=schemas.Comment)
def delete_comment(
        comment_id: int,
        user: models.User = Depends(services.get_current_user),
        db: Session = Depends(get_db)
):
    user_id = user.id
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this comment")
    delete_comment_from_db(db=db, comment_id=comment_id)


@comments_router.get("/comments/comments-daily-breakdown/", response_model=List[dict])
def get_comments_daily_breakdown(
    date_from: str,
    date_to: str,
    db: Session = Depends(get_db),
):
    return comments_analysis(db=db, date_from=date_from, date_to=date_to)
