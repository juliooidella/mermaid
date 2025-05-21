# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the pip cache, which reduces the image size.
# --trusted-host pypi.python.org: Can be useful if there are issues with SSL/TLS for PyPI.
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Copy the rest of the backend application code into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
# This is the port Gunicorn will listen on, and also what app.py might use for dev.
EXPOSE 5000

# Define environment variables (can be overridden at runtime)
# FLASK_ENV is often 'production' for Gunicorn, but app.py logic uses it for debug.
# Gunicorn itself is a production server.
ENV FLASK_ENV="production"
ENV PORT="5000"
# Ensure PYTHONUNBUFFERED is set so logs are sent straight to terminal
ENV PYTHONUNBUFFERED=1

# Command to run the application using Gunicorn with gevent workers
# -w 4: Specifies 4 worker processes. Adjust as needed.
# -b 0.0.0.0:5000: Binds Gunicorn to all network interfaces on port 5000.
# "app:app": Tells Gunicorn to look for an object named 'app' in a Python module named 'app.py'.
# --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker: For Flask-Sockets with Gunicorn
# Or using default gevent worker if app.py itself configures the gevent monkey patching.
# The app.py currently uses gevent.pywsgi.WSGIServer directly in its __main__ block.
# For Docker, it's cleaner to let Gunicorn manage the server.
# The command in app.py's __main__ is:
# server = pywsgi.WSGIServer(('0.0.0.0', int(os.getenv("PORT", 5000))), app, handler_class=WebSocketHandler)
# This implies Gunicorn should also use a gevent-compatible worker.
# Gunicorn has a `gevent` worker class. For Flask-Sockets, often `geventwebsocket.gunicorn.workers.GeventWebSocketWorker` is used,
# but let's try with the standard `gevent` worker first as `gevent-websocket` dependency is already there.
# The `app:app` needs to point to the Flask app instance. Assuming `app.py` defines `app = Flask(__name__)`
# and `sockets.init_app(app)` is called.

# If app.py's __main__ block is the intended entry point for gevent server:
# CMD ["python", "app.py"]
# However, Gunicorn is more standard for Dockerized Flask apps.
# Let's ensure Gunicorn runs the app correctly with gevent for WebSockets.
# The `geventwebsocket.handler.WebSocketHandler` is for pywsgi.
# Gunicorn's gevent worker is just `--worker-class gevent`. Flask-Sockets should work with this.

CMD ["gunicorn", "-w", "4", "--worker-class", "gevent", "-b", "0.0.0.0:5000", "app:app"]
