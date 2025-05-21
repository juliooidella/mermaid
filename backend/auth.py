import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Placeholder for database connection - in a real app, manage this connection carefully
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def get_user_by_google_id(google_id: str):
    """Fetches a user by their Google ID."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE google_id = %s", (google_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_user_by_email(email: str):
    """Fetches a user by their email."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def create_user(google_id: str, name: str, email: str, profile_pic_url: str = None):
    """Creates a new user in the database."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    # Assuming your users table has 'google_id', 'username' (can be name), 'email', 'profile_pic_url'
    # And that password_hash is not required if using Google OAuth primarily
    cursor.execute(
        """
        INSERT INTO users (google_id, username, email, profile_pic_url)
        VALUES (%s, %s, %s, %s)
        RETURNING *;
        """,
        (google_id, name, email, profile_pic_url)
    )
    new_user = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return new_user

def get_or_create_user(user_info: dict):
    """
    Gets an existing user or creates a new one based on Google profile information.
    The `user_info` dict is expected to come from Authlib's `userinfo()` endpoint.
    It typically contains 'sub' (subject, Google's ID for the user), 'name', 'email', 'picture'.
    """
    google_id = user_info.get('sub')
    email = user_info.get('email')
    name = user_info.get('name', email) # Use email as name if name is not provided
    profile_pic = user_info.get('picture')

    if not google_id or not email:
        raise ValueError("Google ID or email missing from user info.")

    # Try to find user by Google ID first
    user = get_user_by_google_id(google_id)
    if user:
        # Optionally, update user's name or profile picture if they've changed
        # For example:
        # if user['username'] != name or user.get('profile_pic_url') != profile_pic:
        #     update_user_details(user['user_id'], name, profile_pic)
        return user

    # If not found by Google ID, try by email (in case they registered differently before)
    # Be cautious with this if emails are not strictly verified or unique across OAuth providers
    user = get_user_by_email(email)
    if user:
        # If found by email, it's good practice to link their Google ID now
        # For example:
        # link_google_id_to_user(user['user_id'], google_id)
        # For simplicity, we'll assume if email matches, it's the same user and update their google_id
        # Or, if your policy is stricter, this could be an error or merge-account scenario.
        # For now, let's assume we create a new one if google_id doesn't match,
        # or handle it as an update if the table structure supports it (e.g. google_id can be NULL).
        # The current create_user function expects google_id, so direct creation is simpler here.
        pass # Fall through to create if no user with that google_id

    # Create new user
    # Note: The 'users' table needs a 'google_id' column.
    # The schema in init.sql had username, email, password_hash.
    # It needs to be adjusted for OAuth. Let's assume 'username' can store 'name',
    # and 'password_hash' can be nullable. A 'google_id' column is crucial.
    # I will proceed assuming the `users` table will be updated to include `google_id VARCHAR(255) UNIQUE`
    # and `profile_pic_url VARCHAR(255)`.
    # I will also assume `password_hash` can be NULL for OAuth users.

    try:
        new_user = create_user(google_id=google_id, name=name, email=email, profile_pic_url=profile_pic)
        return new_user
    except psycopg2.Error as e:
        # Handle potential database errors (e.g., unique constraint violation if somehow missed)
        print(f"Database error: {e}")
        # In a real app, log this and potentially raise a custom exception
        return None

# Example of how you might update the users table structure:
# ALTER TABLE users ADD COLUMN google_id VARCHAR(255) UNIQUE;
# ALTER TABLE users ADD COLUMN profile_pic_url VARCHAR(255);
# ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;
# (These would be run directly on the DB or in a migration script)
