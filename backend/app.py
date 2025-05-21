import os
from functools import wraps
from flask import Flask, redirect, url_for, session, jsonify, request, Blueprint
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

# Assuming auth.py is in a 'backend' package or same directory
from backend.auth import get_or_create_user 
# Import Blueprint modules
from backend.projects_api import projects_bp
from backend.diagrams_api import diagrams_bp
from backend.sharing_api import sharing_bp
from backend.sockets import sockets # Import the Sockets object

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Ensure FLASK_SECRET_KEY is set, otherwise raise an error
if not os.getenv("FLASK_SECRET_KEY"):
    raise RuntimeError("FLASK_SECRET_KEY is not set in the environment.")
if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
    app.logger.warning("Google OAuth credentials are not set. Authentication will not work.")
if not os.getenv("DATABASE_URL"):
    app.logger.warning("DATABASE_URL is not set. Database operations will fail.")

app.secret_key = os.getenv("FLASK_SECRET_KEY") 
app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',  # Mitigate CSRF
    SESSION_COOKIE_SECURE=True if os.getenv('FLASK_ENV') == 'production' else False, # Use secure cookies in production
)

# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify(error="Authentication required. Please login."), 401
        # You could add more checks here, e.g., user active status from DB
        return f(*args, **kwargs)
    return decorated_function

# --- Error Handlers ---
@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e.description) if hasattr(e, 'description') else "Bad request"), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify(error=str(e.description) if hasattr(e, 'description') else "Unauthorized"), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify(error=str(e.description) if hasattr(e, 'description') else "Forbidden"), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify(error=str(e.description) if hasattr(e, 'description') else "Not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    # Log the error e for debugging
    app.logger.error(f"Internal Server Error: {e}")
    return jsonify(error="Internal server error"), 500

@app.errorhandler(PermissionError) # Custom permission error from db_utils
def handle_permission_error(e):
    app.logger.warning(f"Permission denied: {e}")
    return jsonify(error=str(e)), 403


# Initialize OAuth
oauth = OAuth(app)
# Ensure this is placed after app is defined and configured

# Register Google OAuth client
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # OpenID Connect userinfo endpoint
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",  # For ID token validation
)

# --- Basic Routes (Login, Logout, Profile) ---
@app.route('/')
def index():
    user = session.get('user')
    if user:
        return jsonify(message=f"Hello, {user.get('name', user.get('email'))}!", authenticated=True, user_info=user)
    return jsonify(message="Welcome! Please login.", authenticated=False)

@app.route('/login/google')
def login_google():
    # Construct the redirect_uri. Make sure your Google Cloud Console credentials
    # have this URI whitelisted.
    # For local development, it's often http://localhost:5000/auth/google/callback
    # For production, it will be your actual domain.
    redirect_uri = url_for('auth_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def auth_google_callback():
    try:
        token = google.authorize_access_token()
    except Exception as e:
        app.logger.error(f"Error authorizing access token: {e}")
        return jsonify(error="Failed to authorize access token", details=str(e)), 400

    if not token:
        return jsonify(error="Access token not found."), 400
    
    # The userinfo_endpoint automatically uses the token to fetch user info
    # user_info = google.userinfo(token=token) # This is done implicitly by some versions of Authlib or can be explicit
    # Alternatively, parse the ID token if available and configured
    user_info_response = google.get('userinfo')
    if not user_info_response.ok:
        app.logger.error(f"Failed to fetch user info: {user_info_response.text}")
        return jsonify(error="Failed to fetch user information from Google."), 500
        
    user_info = user_info_response.json()

    # Check if DATABASE_URL is set (required by auth.py)
    if not os.getenv("DATABASE_URL"):
        app.logger.error("DATABASE_URL is not set. Cannot connect to database.")
        # In a real app, you might redirect to an error page or return a more user-friendly error
        return jsonify(error="Server configuration error: Database URL not set."), 500

    try:
        user = get_or_create_user(user_info)
        if user:
            # Store user info in session (using RealDictCursor, user is a dict)
            session['user'] = {
                'user_id': user.get('user_id'),
                'google_id': user.get('google_id'),
                'email': user.get('email'),
                'name': user.get('username'), # Assuming 'username' field stores the name
                'profile_pic_url': user.get('profile_pic_url')
            }
            return redirect(url_for('profile'))
        else:
            return jsonify(error="Could not retrieve or create user."), 500
    except Exception as e:
        app.logger.error(f"Error in get_or_create_user: {e}")
        return jsonify(error="An error occurred during user processing.", details=str(e)), 500


@app.route('/profile')
@login_required # Protect the profile route
def profile():
    user = session.get('user') # Already checked by @login_required
    return jsonify(user=user)

@app.route('/logout')
@login_required # User must be logged in to log out
def logout():
    session.pop('user', None)
    # Optionally, could also try to revoke Google's token if necessary,
    # but usually clearing the session is sufficient for web apps.
    return jsonify(message="Logout successful"), 200


# --- API Blueprint Registration ---
# Register Blueprints
app.register_blueprint(projects_bp, url_prefix='/api')
app.register_blueprint(diagrams_bp, url_prefix='/api') # Diagrams are routed like /api/projects/<id>/diagrams and /api/diagrams/<id>
app.register_blueprint(sharing_bp, url_prefix='/api')  # Sharing routes are /api/projects/<id>/sharing


# Initialize Flask-Sockets with the app
sockets.init_app(app)

# --- Main Execution ---
if __name__ == '__main__':
    is_debug_mode = os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == '1'
    
    if not is_debug_mode:
        # Production or staging with gevent
        from gevent import pywsgi
        from geventwebsocket.handler import WebSocketHandler
        print("Starting gevent WSGI server with WebSocket support...")
        server = pywsgi.WSGIServer(('', int(os.getenv("PORT", 5000))), app, handler_class=WebSocketHandler)
        server.serve_forever()
    else:
        # Development server (Flask's default server can work with Flask-Sockets for basic testing,
        # but gevent is more robust for WebSockets)
        # For simplicity in this environment, we'll rely on Flask-Sockets's compatibility
        # with the dev server. If issues arise, a full gevent setup would be needed even for dev.
        print("Starting Flask development server with WebSocket support...")
        # The Flask dev server itself doesn't natively support WebSockets in a way Flask-Sockets
        # always seamlessly integrates without gevent. However, Flask-Sockets tries to make it work.
        # For true robustness, gevent is preferred.
        # The `app.run` might not be sufficient for production-like WebSocket behavior.
        # Flask-Sockets documentation typically shows running with gevent.
        # Let's try to run with Flask dev server and see if Flask-Sockets handles it.
        # If not, the user running this would need to use `python app.py` and have gevent setup.
        # For the tool environment, `app.run` is what's typically invoked by tools.
        # However, for Flask-Sockets, it's better to use its server or gevent.
        # The prompt implies the environment should be able to handle this.
        # If `flask run` is used, it won't use this `if __name__ == '__main__'` block.
        # We will assume `python app.py` is the execution method.
        
        # To ensure WebSockets work with the dev server, we'd typically use a specific setup
        # that Flask-Sockets provides or just use gevent directly.
        # A common way for dev with Flask-Sockets is:
        # from flask_sockets import Sockets
        # sockets = Sockets(app) at global scope
        # And then using a WSGI server that supports it.
        # The current structure with sockets.init_app(app) and then app.run() might be problematic
        # for the dev server.
        # The most reliable way is to use gevent for serving.
        try:
            from gevent import pywsgi
            from geventwebsocket.handler import WebSocketHandler
            print(f"Starting gevent WSGI server on port {os.getenv('PORT', 5000)} in debug mode (less optimal but functional)...")
            server = pywsgi.WSGIServer(('0.0.0.0', int(os.getenv("PORT", 5000))), app, handler_class=WebSocketHandler)
            server.serve_forever()
        except ImportError:
            print("gevent not found. Falling back to Flask's default development server.")
            print("WebSockets may not work correctly with the default Flask dev server without gevent.")
            app.run(debug=is_debug_mode, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
