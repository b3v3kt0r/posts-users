# Posts, comments management API

FastAPI project for managing posts, comments, users.

## Installation

```shell
# Clone the repository
git clone https://github.com/b3v3kt0r/posts-users

# Set up .env file
You have create .env using .env.sample. like example

# Install requirements
pip install -r requirements.txt

# Migrate the database
alembic upgrade head

# Run the server
python -m uvicorn main:app --reload

# Test it via documentation on
http://127.0.0.1:8000/docs
```

## Features

* JWT authenticated.
* Perspective AI for checking comments.
* Cohere AI for auto reply comments.
* CRUD implementation for posts, comments.


## Contact
For contact me:
* Fullname: Stanislav Sudakov
* Email: stanislav.v.sudakov@gmail.com
* Telegram: @sssvvvff