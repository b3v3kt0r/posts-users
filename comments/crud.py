import os
from datetime import datetime

from dotenv import load_dotenv
from googleapiclient import discovery
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
