# Mermaid Diagram Editor

## Project Overview

The Mermaid Diagram Editor is a web-based application that allows users to create, edit, and manage diagrams using the Mermaid.js syntax. It features user authentication via Google OAuth, project and diagram management, and basic real-time collaboration for editing diagrams. The application is fully containerized using Docker and Docker Compose for easy setup and deployment.

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
2.  **Docker Compose**: [Install Docker Compose](https://docs.docker.com/compose/install/) (Usually included with Docker Desktop).
3.  **Google OAuth2 Client ID and Secret**:
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   Navigate to "APIs & Services" > "Credentials".
    *   Click "Create Credentials" > "OAuth client ID".
    *   Choose "Web application" as the application type.
    *   **Authorized JavaScript origins**: Add `http://localhost:8080` (or your frontend's host and port if different).
    *   **Authorized redirect URIs**: Add `http://localhost:5000/auth/google/callback` (this is your backend's callback URL).
    *   Click "Create". You will be shown your Client ID and Client Secret. Keep these safe.

## Setup

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Configure Google OAuth Credentials**:
    *   Open the `docker-compose.yml` file located in the project root.
    *   Find the `backend` service definition.
    *   Locate the following environment variables:
        ```yaml
        # GOOGLE_CLIENT_ID: "YOUR_GOOGLE_CLIENT_ID_HERE"
        # GOOGLE_CLIENT_SECRET: "YOUR_GOOGLE_CLIENT_SECRET_HERE"
        ```
    *   Uncomment these lines (remove the `#`) and replace `"YOUR_GOOGLE_CLIENT_ID_HERE"` and `"YOUR_GOOGLE_CLIENT_SECRET_HERE"` with the actual Client ID and Client Secret you obtained from the Google Cloud Console.
    *   **Important**: It's also recommended to change the `FLASK_SECRET_KEY` in `docker-compose.yml` for any production-like environment.

3.  **Database Credentials (Optional)**:
    *   The `docker-compose.yml` file uses default credentials (`user`, `password`, `mydatabase`) for the PostgreSQL database. If you wish to change these, update them in the `db` service's `environment` section AND ensure the `DATABASE_URL` in the `backend` service's `environment` section reflects these changes.

## Running the Application

1.  **Build and Start Services**:
    Open your terminal in the project root directory (where `docker-compose.yml` is located) and run:
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker images for the frontend and backend services (if they don't exist or have changed) and then start all services defined in the `docker-compose.yml` file. Wait for the services to initialize. You should see logs from `db`, `backend`, and `frontend`. The backend will wait for the database to be healthy before starting.

2.  **Accessing the Application**:
    *   **Frontend**: Open your web browser and navigate to `http://localhost:8080`.
    *   **Backend API (for developers/testing)**: The backend API is accessible at `http://localhost:5000`. You can test API endpoints using tools like Postman or curl.

## Testing and Verification Steps

1.  **Access Frontend**:
    *   Go to `http://localhost:8080` in your browser. You should see the "Welcome to the Mermaid Diagram Editor" page.

2.  **Login**:
    *   Click the "Login with Google" button.
    *   You should be redirected to the Google OAuth consent screen.
    *   Log in with your Google account and grant permissions if prompted.
    *   Upon successful login, you should be redirected back to the application and see the "My Projects" view, with your username displayed in the navigation bar.

3.  **Create a New Project**:
    *   In the "My Projects" view, click the "Create New Project" button.
    *   Enter a name for your project (e.g., "My Test Project") in the prompt and click "OK".
    *   The new project should appear in the list.

4.  **Create a New Diagram**:
    *   Click on the project you just created (e.g., "My Test Project").
    *   You should be taken to the "Diagrams in Project: [Project Name]" view.
    *   Click the "Create New Diagram" button.
    *   Enter a name for your diagram (e.g., "Flowchart 1") in the prompt and click "OK".
    *   The new diagram should appear in the list for that project.

5.  **Edit and Render Mermaid Code**:
    *   Click on the diagram you just created (e.g., "Flowchart 1").
    *   You will be taken to the editor view.
    *   In the "Mermaid Code" textarea on the left, enter or modify Mermaid syntax. For example:
        ```mermaid
        graph TD;
            A[Start] --> B{Is it?};
            B -- Yes --> C[OK];
            C --> D[End];
            B -- No --> E[Not OK];
            E --> D;
        ```
    *   As you type (after a short delay), the rendered diagram should appear on the right.
    *   If there are syntax errors in your Mermaid code, an error message should be displayed in the output area, including the problematic code.
    *   Click the "Save Diagram" button to persist your changes.

6.  **Test Real-Time Collaboration**:
    *   Open the same diagram (e.g., "Flowchart 1" from "My Test Project") in two separate browser windows or tabs.
    *   Make changes to the Mermaid code in one window/tab.
    *   The changes should automatically reflect in the textarea and the rendered diagram in the other window/tab after a brief moment.

7.  **Verify Data Persistence**:
    *   With some projects and diagrams created, go back to your terminal where `docker-compose up` is running.
    *   Press `Ctrl+C` to stop the application.
    *   Then run `docker-compose down` to fully stop and remove the containers (but not the named volume `pg_data`).
    *   Restart the application: `docker-compose up` (the `--build` flag is not necessary if no code has changed).
    *   Access the frontend at `http://localhost:8080` and log in again.
    *   Your previously created projects and diagrams should still be listed, and their content should be intact.

## Stopping the Application

1.  To stop all services and remove the containers, networks, and (optionally) volumes:
    *   If `docker-compose up` is running in your terminal, press `Ctrl+C`.
    *   Then, run:
        ```bash
        docker-compose down
        ```
    *   To remove named volumes as well (like `pg_data`, which would delete all database data), use:
        ```bash
        docker-compose down -v
        ```

## Project Structure

```
.
├── backend/                # Python/Flask backend application
│   ├── Dockerfile          # Dockerfile for the backend
│   ├── requirements.txt    # Python dependencies
│   ├── app.py              # Main Flask application file
│   ├── auth.py             # Authentication logic
│   ├── db_utils.py         # Database utility functions
│   ├── projects_api.py     # API endpoints for projects
│   ├── diagrams_api.py     # API endpoints for diagrams
│   ├── sharing_api.py      # API endpoints for sharing
│   └── sockets.py          # WebSocket handling
├── database/               # Database related files
│   └── init.sql            # PostgreSQL schema initialization script
├── frontend/               # Static frontend application (HTML, CSS, JS)
│   ├── Dockerfile          # Dockerfile for the frontend (Nginx)
│   ├── index.html          # Main HTML file
│   ├── style.css           # CSS styles
│   ├── app.js              # Main frontend JavaScript logic
│   ├── api.js              # JS for backend API communication (mocked/real)
│   ├── ui.js               # JS for DOM manipulation
│   └── socketService.js    # JS for WebSocket communication
├── docker-compose.yml      # Docker Compose file for orchestrating services
└── README.md               # This file
```

This `README.md` provides a comprehensive guide for users to set up, run, and test the application.
It includes all the sections requested in the subtask.
