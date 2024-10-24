from sqlalchemy.orm import Session

from posts import models, schemas


def get_all_posts(db: Session):
    return db.query(models.Post).all()


def create_post(db: Session, post: schemas.PostCreate):
    db_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
        auto_replay_enabled=post.auto_replay_enabled,
        auto_replay_delay=post.auto_replay_delay,
        created_at=post.created_at,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post
