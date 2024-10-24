from datetime import datetime

from sqlalchemy.orm import Session

from comments.models import Comment


def get_comments_for_post(db: Session, post_id):
    return db.query(Comment).filter(Comment.post_id == post_id).all()


def create_comment(db: Session, comment: Comment, post_id: int, user_id: int):
    db_comment = Comment(
        content=comment.content,
        post_id=post_id,
        user_id=user_id,
        created_at=datetime.now(),
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment
