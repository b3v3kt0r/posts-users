import pytest
from datetime import datetime, UTC
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.engine import Base, get_db
from main import app  # Assuming your FastAPI app is in main.py
from posts import crud
from posts.models import Post
from users.models import User

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        password="testpassword",
        username="testuser",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_post(db_session, test_user):
    post = Post(
        title="Test Post",
        content="Test Content",
        user_id=test_user.id,
        auto_replay_enabled=False,
        auto_replay_delay=0,
        created_at=datetime.now(UTC)
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return post


# CRUD Tests
def test_get_all_posts_empty(db_session):
    posts = crud.get_all_posts(db_session)
    assert posts == []


def test_get_all_posts(db_session, test_post):
    posts = crud.get_all_posts(db_session)
    assert len(posts) == 1
    assert posts[0].title == "Test Post"
    assert posts[0].content == "Test Content"


def test_get_post_by_id(db_session, test_post):
    post = crud.get_post_by_id(db_session, test_post.id)
    assert post.title == "Test Post"
    assert post.content == "Test Content"


def test_get_post_by_id_not_found(db_session):
    post = crud.get_post_by_id(db_session, 999)
    assert post is None


def test_create_post(db_session, test_user):
    from posts.schemas import PostCreate

    post_data = PostCreate(
        title="New Post",
        content="New Content",
        auto_replay_enabled=True,
        auto_replay_delay=60
    )

    post = crud.create_post(db_session, post_data, test_user.id)
    assert post.title == "New Post"
    assert post.content == "New Content"
    assert post.user_id == test_user.id
    assert post.auto_replay_enabled is True
    assert post.auto_replay_delay == 60


def test_update_post(db_session, test_post):
    from posts.schemas import Post as PostSchema

    update_data = PostSchema(
        id=test_post.id,
        title="Updated Title",
        content="Updated Content",
        user_id=test_post.user_id,
        auto_replay_enabled=True,
        auto_replay_delay=30,
        created_at=test_post.created_at
    )

    updated_post = crud.update_post_in_db(db_session, update_data, test_post)
    assert updated_post.title == "Updated Title"
    assert updated_post.content == "Updated Content"
    assert updated_post.auto_replay_enabled is True
    assert updated_post.auto_replay_delay == 30


def test_delete_post(db_session, test_post):
    crud.delete_post_from_db(db_session, test_post.id)
    deleted_post = crud.get_post_by_id(db_session, test_post.id)
    assert deleted_post is None


# API Endpoint Tests
def test_get_posts_endpoint(test_post):
    response = client.get("/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) == 1
    assert posts[0]["title"] == "Test Post"


def test_get_post_endpoint(test_post):
    response = client.get(f"/posts/{test_post.id}")
    assert response.status_code == 200
    post = response.json()
    assert post["title"] == "Test Post"


def test_get_post_endpoint_not_found():
    response = client.get("/posts/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"
