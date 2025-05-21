from flask import Blueprint, request, jsonify, session
from backend.db_utils import BaseDBOperations # or specific project DB operations class
# Assuming login_required decorator is accessible, e.g. from app or a shared utils
# If it's in app.py, we might need to pass 'app' or restructure.
# For now, let's assume it can be imported or will be applied at registration in app.py
# from backend.app import login_required # This creates a circular import if app.py imports this.
from backend.app import login_required # Import the shared decorator

projects_bp = Blueprint('projects_api', __name__)
db_ops = BaseDBOperations() # Use the base or a specialized one

@projects_bp.route('/projects', methods=['POST'])
@login_required # Apply decorator
def create_project():
    data = request.get_json()
    if not data or not data.get('project_name'):
        return jsonify(error="Project name is required."), 400

    project_name = data['project_name']
    try:
        user_id = db_ops._get_user_id_from_session(session)
        query = """
            INSERT INTO projects (project_name, user_id) 
            VALUES (%s, %s) RETURNING project_id, project_name, user_id, created_at, updated_at;
        """
        project = db_ops._execute(query, (project_name, user_id), fetchone=True, commit=True)
        return jsonify(project), 201
    except PermissionError as e: # From _get_user_id_from_session
        return jsonify(error=str(e)), 401
    except Exception as e:
        # Log e
        return jsonify(error=f"Failed to create project: {str(e)}"), 500

@projects_bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    try:
        user_id = db_ops._get_user_id_from_session(session)
        # Query projects owned by the user OR shared with the user
        query = """
            SELECT p.project_id, p.project_name, p.user_id, p.created_at, p.updated_at, 'owner' as role
            FROM projects p
            WHERE p.user_id = %s
            UNION
            SELECT p.project_id, p.project_name, p.user_id, p.created_at, p.updated_at, sp.permission_level as role
            FROM projects p
            JOIN sharing_permissions sp ON p.project_id = sp.project_id
            WHERE sp.user_id = %s;
        """
        projects = db_ops._execute(query, (user_id, user_id), fetchall=True)
        return jsonify(projects), 200
    except PermissionError as e:
        return jsonify(error=str(e)), 401
    except Exception as e:
        return jsonify(error=f"Failed to retrieve projects: {str(e)}"), 500

@projects_bp.route('/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    try:
        user_id = db_ops._get_user_id_from_session(session)
        # Check if user owns or has access through sharing_permissions
        query = """
            SELECT p.* FROM projects p
            LEFT JOIN sharing_permissions sp ON p.project_id = sp.project_id
            WHERE p.project_id = %s AND (p.user_id = %s OR sp.user_id = %s);
        """
        project = db_ops._execute(query, (project_id, user_id, user_id), fetchone=True)
        if not project:
            return jsonify(error="Project not found or access denied."), 404
        return jsonify(project), 200
    except PermissionError as e:
        return jsonify(error=str(e)), 401
    except Exception as e:
        return jsonify(error=f"Failed to retrieve project: {str(e)}"), 500

@projects_bp.route('/projects/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    data = request.get_json()
    if not data or not data.get('project_name'):
        return jsonify(error="Project name is required for update."), 400

    new_project_name = data['project_name']
    try:
        user_id = db_ops._get_user_id_from_session(session)
        # First, verify ownership
        project = db_ops._execute("SELECT user_id FROM projects WHERE project_id = %s", (project_id,), fetchone=True)
        if not project:
            return jsonify(error="Project not found."), 404
        db_ops._check_ownership(project['user_id'], user_id, "Only the project owner can update the project name.")

        query = """
            UPDATE projects SET project_name = %s, updated_at = CURRENT_TIMESTAMP
            WHERE project_id = %s AND user_id = %s
            RETURNING project_id, project_name, user_id, created_at, updated_at;
        """
        updated_project = db_ops._execute(query, (new_project_name, project_id, user_id), fetchone=True, commit=True)
        if not updated_project:
            # This case should ideally not be hit if ownership is checked and project exists
            return jsonify(error="Failed to update project or project not found."), 404 
        return jsonify(updated_project), 200
    except PermissionError as e: # Catches both session error and ownership error
        return jsonify(error=str(e)), (401 if "User not authenticated" in str(e) else 403)
    except Exception as e:
        return jsonify(error=f"Failed to update project: {str(e)}"), 500

@projects_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    try:
        user_id = db_ops._get_user_id_from_session(session)
        # Verify ownership before deleting
        project = db_ops._execute("SELECT user_id FROM projects WHERE project_id = %s", (project_id,), fetchone=True)
        if not project:
            return jsonify(error="Project not found."), 404
        db_ops._check_ownership(project['user_id'], user_id, "Only the project owner can delete the project.")

        # Deletion will cascade to diagrams and sharing_permissions due to DB schema
        deleted_count = db_ops._execute("DELETE FROM projects WHERE project_id = %s AND user_id = %s", 
                                        (project_id, user_id), commit=True) # execute_query needs to handle rowcount for DELETE
        
        # The current _execute doesn't directly return rowcount for DELETE in a simple way.
        # Let's assume if no error, it worked. A more robust way is to check cursor.rowcount.
        # For now, we'll assume success if no exception.
        # if deleted_count is None or deleted_count == 0: # Assuming _execute could return rowcount
        #     return jsonify(error="Failed to delete project or project not found."), 404

        return jsonify(message="Project deleted successfully."), 200
    except PermissionError as e:
        return jsonify(error=str(e)), (401 if "User not authenticated" in str(e) else 403)
    except Exception as e:
        # Handle cases like foreign key constraints if not set to cascade, etc.
        return jsonify(error=f"Failed to delete project: {str(e)}"), 500
