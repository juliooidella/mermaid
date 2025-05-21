from flask import Blueprint, request, jsonify, session
from backend.db_utils import BaseDBOperations
from backend.app import login_required # Import the shared decorator

sharing_bp = Blueprint('sharing_api', __name__)
db_ops = BaseDBOperations()

# Helper function to check if the current user owns the project
def check_project_ownership(project_id, current_user_id):
    project_owner_query = "SELECT user_id FROM projects WHERE project_id = %s;"
    project = db_ops._execute(project_owner_query, (project_id,), fetchone=True)
    if not project:
        raise PermissionError("Project not found.") # 404
    if project['user_id'] != current_user_id:
        raise PermissionError("Only the project owner can manage sharing settings.") # 403
    return True


@sharing_bp.route('/projects/<int:project_id>/sharing', methods=['POST'])
@login_required
def add_collaborator(project_id):
    data = request.get_json()
    if not data or not data.get('email') or not data.get('permission_level'):
        return jsonify(error="Email and permission level are required."), 400

    collaborator_email = data['email']
    permission_level = data['permission_level']
    valid_permissions = ['view', 'edit'] # Define valid permission levels
    if permission_level not in valid_permissions:
        return jsonify(error=f"Invalid permission level. Must be one of {valid_permissions}."), 400

    try:
        current_user_id = db_ops._get_user_id_from_session(session)
        check_project_ownership(project_id, current_user_id) # Only owner can share

        # Find the user to share with by email
        collaborator_user = db_ops._execute("SELECT user_id FROM users WHERE email = %s;", (collaborator_email,), fetchone=True)
        if not collaborator_user:
            return jsonify(error=f"User with email {collaborator_email} not found."), 404
        
        collaborator_user_id = collaborator_user['user_id']
        if collaborator_user_id == current_user_id:
            return jsonify(error="Cannot share the project with yourself."), 400

        # Add or update permission
        query = """
            INSERT INTO sharing_permissions (project_id, user_id, permission_level)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id, user_id) DO UPDATE SET permission_level = EXCLUDED.permission_level
            RETURNING permission_id, project_id, user_id, permission_level, created_at;
        """
        permission = db_ops._execute(query, (project_id, collaborator_user_id, permission_level), fetchone=True, commit=True)
        return jsonify(permission), 201
    except PermissionError as e: # Catches session errors and ownership/project not found errors
        status_code = 401 if "User not authenticated" in str(e) or "invalid session" in str(e) \
            else (404 if "Project not found" in str(e) else 403)
        return jsonify(error=str(e)), status_code
    except Exception as e:
        # Catch unique constraint violations if user is already a collaborator (handled by ON CONFLICT now)
        # or other DB errors
        return jsonify(error=f"Failed to add collaborator: {str(e)}"), 500

@sharing_bp.route('/projects/<int:project_id>/sharing', methods=['GET'])
@login_required
def get_shared_with_users(project_id):
    try:
        current_user_id = db_ops._get_user_id_from_session(session)
        # Owner or anyone with access to the project can see who it's shared with
        # Using the check_project_access function from diagrams_api logic (or similar)
        # For simplicity here, we check if user can access the project first.
        access_query = """
            SELECT p.user_id AS owner_id, sp.permission_level
            FROM projects p
            LEFT JOIN sharing_permissions sp ON p.project_id = sp.project_id AND sp.user_id = %s
            WHERE p.project_id = %s;
        """
        access_result = db_ops._execute(access_query, (current_user_id, project_id), fetchone=True)
        if not access_result or (access_result['owner_id'] != current_user_id and not access_result['permission_level']):
             raise PermissionError("Access denied to project sharing information.")


        query = """
            SELECT u.user_id, u.username, u.email, u.profile_pic_url, sp.permission_level
            FROM sharing_permissions sp
            JOIN users u ON sp.user_id = u.user_id
            WHERE sp.project_id = %s;
        """
        shared_users = db_ops._execute(query, (project_id,), fetchall=True)
        return jsonify(shared_users), 200
    except PermissionError as e:
        status_code = 401 if "User not authenticated" in str(e) or "invalid session" in str(e) \
            else (404 if "Project not found" in str(e) else 403)
        return jsonify(error=str(e)), status_code
    except Exception as e:
        return jsonify(error=f"Failed to retrieve sharing information: {str(e)}"), 500

@sharing_bp.route('/projects/<int:project_id>/sharing/<int:shared_user_id>', methods=['PUT'])
@login_required
def update_collaborator_permission(project_id, shared_user_id):
    data = request.get_json()
    if not data or not data.get('permission_level'):
        return jsonify(error="Permission level is required."), 400

    new_permission_level = data['permission_level']
    valid_permissions = ['view', 'edit'] # Define valid permission levels
    if new_permission_level not in valid_permissions:
        return jsonify(error=f"Invalid permission level. Must be one of {valid_permissions}."), 400

    try:
        current_user_id = db_ops._get_user_id_from_session(session)
        check_project_ownership(project_id, current_user_id) # Only owner can change permissions

        if shared_user_id == current_user_id:
            return jsonify(error="Cannot change your own permissions directly via this route."), 400

        query = """
            UPDATE sharing_permissions
            SET permission_level = %s
            WHERE project_id = %s AND user_id = %s
            RETURNING permission_id, project_id, user_id, permission_level, created_at;
        """
        updated_permission = db_ops._execute(query, (new_permission_level, project_id, shared_user_id), fetchone=True, commit=True)
        if not updated_permission:
            return jsonify(error="Collaborator not found for this project or no update was made."), 404
        return jsonify(updated_permission), 200
    except PermissionError as e:
        status_code = 401 if "User not authenticated" in str(e) or "invalid session" in str(e) \
            else (404 if "Project not found" in str(e) else 403)
        return jsonify(error=str(e)), status_code
    except Exception as e:
        return jsonify(error=f"Failed to update permission: {str(e)}"), 500

@sharing_bp.route('/projects/<int:project_id>/sharing/<int:shared_user_id>', methods=['DELETE'])
@login_required
def remove_collaborator(project_id, shared_user_id):
    try:
        current_user_id = db_ops._get_user_id_from_session(session)
        check_project_ownership(project_id, current_user_id) # Only owner can remove collaborators

        if shared_user_id == current_user_id:
            return jsonify(error="Cannot remove yourself as a collaborator via this route."), 400
        
        # The _execute method needs to be able to return info about deletion success.
        # Assuming it raises an error for failure or returns None/0 if nothing deleted.
        # For psycopg2, cursor.rowcount gives number of rows affected.
        delete_query = "DELETE FROM sharing_permissions WHERE project_id = %s AND user_id = %s;"
        # We need to modify _execute or have a specific method in db_ops that returns rowcount for DELETE.
        # For now, let's assume it works and if record not found, no error, but nothing happens.
        # A better check would be to see if the permission existed first.
        
        # Check if permission exists
        perm_exists = db_ops._execute("SELECT 1 FROM sharing_permissions WHERE project_id = %s AND user_id = %s", (project_id, shared_user_id), fetchone=True)
        if not perm_exists:
            return jsonify(error="Collaborator not found for this project."), 404

        db_ops._execute(delete_query, (project_id, shared_user_id), commit=True)
        return jsonify(message="Collaborator removed successfully."), 200
    except PermissionError as e:
        status_code = 401 if "User not authenticated" in str(e) or "invalid session" in str(e) \
            else (404 if "Project not found" in str(e) else 403)
        return jsonify(error=str(e)), status_code
    except Exception as e:
        return jsonify(error=f"Failed to remove collaborator: {str(e)}"), 500
