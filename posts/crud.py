from datetime import datetime

from sqlalchemy.orm import Session

from posts import models, schemas


def get_all_posts(db: Session):
    posts = db.query(models.Post).all()
    if posts:
        return posts
    return []


def get_post_by_id(db: Session, id: int):
    return db.query(models.Post).filter(models.Post.id == id).first()


def create_post(db: Session, post: schemas.PostCreate, user_id: int):
    db_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=user_id,
        auto_replay_enabled=post.auto_replay_enabled,
        auto_replay_delay=post.auto_replay_delay,
        created_at=datetime.now()
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_post_in_db(db: Session, post_data, post):
    post.title = post_data.title or post.title
    post.content = post_data.content or post.content
    post.auto_replay_enabled = post_data.auto_replay_enabled if post_data.auto_replay_enabled is not None else post.auto_replay_enabled
    post.auto_replay_delay = post_data.auto_replay_delay or post.auto_replay_delay

    db.commit()
    db.refresh(post)

    return post


def delete_post_from_db(db: Session, post_id: int):
    db.delete(get_post_by_id(db, post_id))
    db.commit()
