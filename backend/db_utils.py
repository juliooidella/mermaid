import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Establishes a connection to the database."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Example of a helper function to execute queries
def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Executes a SQL query and returns results.
    Manages connection and cursor.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        
        result = None
        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        
        if commit:
            conn.commit()
            # For INSERT, UPDATE, DELETE returning ID or affected row,
            # result might be already set if RETURNING is used.
            # If not, cursor.rowcount can be useful.
            if result is None and (query.strip().upper().startswith("INSERT") or \
                                   query.strip().upper().startswith("UPDATE") or \
                                   query.strip().upper().startswith("DELETE")):
                # If RETURNING was used, fetchone/fetchall would have captured it.
                # If not, rowcount gives number of affected rows.
                # For simplicity, if a specific return is needed, use RETURNING in query and fetchone.
                pass


        return result
    except psycopg2.Error as e:
        if conn and not commit: # Only rollback if not a commit error itself
            conn.rollback()
        # Log error e
        print(f"Database query error: {e}") # Replace with proper logging
        raise # Re-raise the exception to be handled by the caller
    finally:
        if conn:
            conn.close()

class BaseDBOperations:
    """
    Base class for database operations to inherit common utilities like execute_query.
    """
    def _execute(self, query, params=None, fetchone=False, fetchall=False, commit=False):
        # This method provides a shorthand for subclasses
        return execute_query(query, params, fetchone, fetchall, commit)

    def _get_user_id_from_session(self, session):
        """Helper to get user_id from session, raises error if not found."""
        user = session.get('user')
        if not user or 'user_id' not in user:
            # This should ideally result in a 401 error if hit in a request context
            raise PermissionError("User not authenticated.") 
        return user['user_id']

    def _check_ownership(self, record_user_id, current_user_id, message="User does not own this resource."):
        """Checks if the current user owns the record."""
        if record_user_id != current_user_id:
            raise PermissionError(message) # This should be caught and turned into a 403 error

# Note: The PermissionError raised here should be handled by the API routes
# to return appropriate HTTP status codes (e.g., 401 for authentication, 403 for permission denied).
# Flask's error handlers can be used for this.
