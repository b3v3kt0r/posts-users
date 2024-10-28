import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from comments.crud import (
    check_for_toxicity,
    comments_analysis,
    auto_replay_for_comments,
    create_comment,
    update_comment_in_db,
    delete_comment_from_db,
)
from comments.models import Comment
from comments.schemas import CommentCreate
from posts.models import Post
from users.models import User


@pytest.fixture
def db_session():
    return Mock(spec=Session)


@pytest.fixture
def test_user():
    return User(id=1, username="testuser", email="test@example.com")


@pytest.fixture
def test_post():
    return Post(
        id=1,
        title="Test Post",
        content="Test Content",
        user_id=1,
        auto_replay_enabled=True,
        auto_replay_delay=60
    )


@pytest.fixture
def test_comment():
    return Comment(
        id=1,
        content="Test comment",
        user_id=1,
        post_id=1,
        is_blocked=False,
        created_at=datetime.now(UTC)
    )


# Test CRUD Operations
def test_create_comment_success(db_session):
    test_comment_data = Comment(
        content="New comment",
        post_id=1,
        user_id=1,
        created_at=datetime.now(UTC)
    )

    result = create_comment(
        db=db_session,
        comment=test_comment_data,
        post_id=1,
        user_id=1
    )

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()
    assert result.content == "New comment"
    assert result.post_id == 1
    assert result.user_id == 1


def test_update_comment_success(db_session, test_comment):
    updated_content = Comment(content="Updated content")

    result = update_comment_in_db(
        db=db_session,
        comment=test_comment,
        comment_data=updated_content
    )

    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()
    assert result == test_comment


def test_delete_comment_success(db_session, test_comment):
    db_session.query.return_value.filter.return_value.first.return_value = test_comment

    delete_comment_from_db(db=db_session, comment_id=1)

    db_session.delete.assert_called_once_with(test_comment)
    db_session.commit.assert_called_once()


# Test Toxicity Check
@patch('comments.crud.discovery')
def test_check_for_toxicity(mock_discovery):
    mock_client = Mock()
    mock_discovery.build.return_value = mock_client

    mock_response = {
        "attributeScores": {
            "TOXICITY": {
                "spanScores": [{"score": {"value": 0.8}}]
            }
        }
    }

    mock_client.comments.return_value.analyze.return_value.execute.return_value = mock_response

    result = check_for_toxicity("This is a toxic comment")
    assert result is True


# Test Comments Analysis
def test_comments_analysis(db_session):
    mock_results = [
        Mock(
            day="2024-03-01",
            total_comments=10,
            blocked_comments=2
        ),
        Mock(
            day="2024-03-02",
            total_comments=15,
            blocked_comments=3
        )
    ]

    db_session.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = mock_results

    result = comments_analysis(
        db=db_session,
        date_from="2024-03-01",
        date_to="2024-03-02"
    )

    assert len(result) == 2
    assert result[0]["total_comments"] == 10
    assert result[0]["blocked_comments"] == 2
    assert result[1]["total_comments"] == 15
    assert result[1]["blocked_comments"] == 3


# Test Auto Reply
@patch('comments.crud.cohere.ClientV2')
def test_auto_replay_for_comments(mock_cohere_client, db_session):
    mock_client = Mock()
    mock_cohere_client.return_value = mock_client

    mock_response = {
        "message": [
            [None, None, None],
            [None, None, None],
            [None, None, None],
            [None, [(None, "Auto-generated reply")]]
        ]
    }
    mock_client.chat.return_value = mock_response

    auto_replay_for_comments(
        db=db_session,
        comment="Test comment",
        post_id=1,
        delay=0,
        author_id=1
    )

    mock_client.chat.assert_called_once_with(
        model="command-r-plus",
        messages=[{
            "role": "user",
            "content": "Give a response for this comment: Test comment"
        }]
    )


# Test API Endpoints
def test_get_comments_for_post_endpoint(db_session, test_comment):
    db_session.query.return_value.filter.return_value.all.return_value = [test_comment]

    from comments.routers import get_comments_for_post

    response = get_comments_for_post(post_id=1, db=db_session)
    assert len(response) == 1
    assert response[0] == test_comment


def test_get_comments_for_post_not_found(db_session):
    db_session.query.return_value.filter.return_value.all.return_value = []

    from comments.routers import get_comments_for_post

    with pytest.raises(HTTPException) as exc_info:
        get_comments_for_post(post_id=999, db=db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Comments not found"


def test_create_comment_endpoint(db_session, test_user, test_post):
    comment_data = CommentCreate(content="New comment", is_blocked=False)
    db_session.query.return_value.filter.return_value.first.return_value = test_post

    from comments.routers import create_comment as create_comment_endpoint

    with patch('comments.crud.check_for_toxicity', return_value=False):
        response = create_comment_endpoint(
            post_id=1,
            comment=comment_data,
            user=test_user,
            db=db_session
        )

        assert response.content == comment_data.content
        assert not response.is_blocked


def test_delete_comment_endpoint(db_session, test_user, test_comment):
    db_session.query.return_value.filter.return_value.first.return_value = test_comment

    from comments.routers import delete_comment as delete_comment_endpoint

    delete_comment_endpoint(comment_id=1, user=test_user, db=db_session)

    db_session.delete.assert_called_once()
    db_session.commit.assert_called_once()


# Test for edge cases
def test_update_comment_not_found(db_session, test_user):
    db_session.query.return_value.filter.return_value.first.return_value = None

    from comments.routers import update_comment

    with pytest.raises(HTTPException) as exc_info:
        update_comment(
            comment_id=999,
            comment_data=CommentCreate(content="Updated content"),
            user=test_user,
            db=db_session
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Comment not found"


def test_update_comment_unauthorized(db_session, test_user, test_comment):
    test_comment.user_id = 999  # Different user
    db_session.query.return_value.filter.return_value.first.return_value = test_comment

    from comments.routers import update_comment

    with pytest.raises(HTTPException) as exc_info:
        update_comment(
            comment_id=1,
            comment_data=CommentCreate(content="Updated content"),
            user=test_user,
            db=db_session
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "You are not allowed to edit this comment"
