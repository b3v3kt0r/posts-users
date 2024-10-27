import os
from datetime import datetime

from dotenv import load_dotenv
from googleapiclient import discovery
from sqlalchemy import func, and_, case
from sqlalchemy.orm import Session

from comments.models import Comment

load_dotenv()

api_key = os.environ.get("PERSPECTIVE_API_KEY")


def check_for_toxicity(comment):
    client = discovery.build(
        "commentanalyzer",
        "v1alpha1",
        developerKey=api_key,
        discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
        static_discovery=False,
    )

    analyze_request = {
        'comment': {'text': comment},
        'requestedAttributes': {'TOXICITY': {}}
    }

    response = client.comments().analyze(body=analyze_request).execute()

    if response["attributeScores"]["TOXICITY"]["spanScores"][0]["score"]["value"] > 0.7:
        return True
    return False


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


def update_comment_in_db(db: Session, comment: Comment, comment_data):
    comment.content = comment.content or comment_data.content

    db.commit()
    db.refresh(comment)
    return comment


def delete_comment_from_db(db: Session, comment_id: int):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    db.delete(comment)
    db.commit()


def comments_analysis(db: Session, date_from: str, date_to: str):
    date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
    date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")

    results = (
        db.query(
            func.strftime("%Y-%m-%d", Comment.created_at).label("day"),
            func.count(Comment.id).label("total_comments"),
            func.sum(
                case(
                    (Comment.is_blocked == True, 1),
                    else_=0
                )
            ).label("blocked_comments"),
        )
        .filter(and_(Comment.created_at >= date_from_dt, Comment.created_at < date_to_dt))
        .group_by(func.strftime("%Y-%m-%d", Comment.created_at))
        .order_by("day")
        .all()
    )

    return [
        {
            "day": result.day,
            "total_comments": result.total_comments,
            "blocked_comments": result.blocked_comments or 0,
        }
        for result in results
    ]
