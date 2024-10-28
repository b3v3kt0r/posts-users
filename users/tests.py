import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from jose import jwt

from database.engine import Base, get_db
from main import app
from users.services import SECRET_KEY, ALGORITHM, hase_password
from users.models import User

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
def test_db():
    # Bind the testing database session
    db = TestingSessionLocal()
    # Clear the database before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def create_test_user(test_db):
    user = User(
        username="testuser",
        email="test@example.com",
        password=hase_password("testpassword")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


def test_register_success():
    response = client.post(
        "/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123"
        }
    )
    assert response.status_code == 201
    assert response.json() == {"message": "User created successfully"}


def test_register_duplicate_username(create_test_user):
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_register_duplicate_email(create_test_user):
    response = client.post(
        "/register",
        json={
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(create_test_user):
    response = client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "testpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Verify token contents
    payload = jwt.decode(token_data["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"


def test_login_wrong_password(create_test_user):
    response = client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user():
    response = client.post(
        "/token",
        data={
            "username": "nonexistent",
            "password": "password123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_password_hashing():
    from users.services import verify_password, hase_password

    password = "testpassword123"
    hashed = hase_password(password)

    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)
