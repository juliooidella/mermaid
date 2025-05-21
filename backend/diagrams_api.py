from flask import Blueprint, request, jsonify, session
from backend.db_utils import BaseDBOperations
from backend.app import login_required # Import the shared decorator

diagrams_bp = Blueprint('diagrams_api', __name__)
db_ops = BaseDBOperations()

# Helper function to check project access (view or edit)
def check_project_access(project_id, user_id, require_edit=False):
    permission_query = """
        SELECT p.user_id AS owner_id, sp.permission_level
        FROM projects p
        LEFT JOIN sharing_permissions sp ON p.project_id = sp.project_id AND sp.user_id = %s
        WHERE p.project_id = %s;
    """
    result = db_ops._execute(permission_query, (user_id, project_id), fetchone=True)

    if not result:
        raise PermissionError("Project not found.") # 404

    is_owner = result['owner_id'] == user_id
    permission_level = result['permission_level']

    if is_owner:
        return True # Owner has all permissions

    if require_edit:
        if permission_level not in ['edit', 'admin']: # Assuming 'admin' is a possible higher permission
            raise PermissionError("You do not have permission to modify this project's diagrams.") # 403
    elif not permission_level and not is_owner: # No direct ownership, no sharing permission
         raise PermissionError("You do not have permission to view this project's diagrams.") # 403
    
    # If require_edit is False, any permission_level (e.g., 'view') or ownership is enough
    return True


@diagrams_bp.route('/projects/<int:project_id>/diagrams', methods=['POST'])
@login_required
def create_diagram(project_id):
    data = request.get_json()
    if not data or not data.get('diagram_name'):
        return jsonify(error="Diagram name is required."), 400
    
    diagram_name = data['diagram_name']
    diagram_data = data.get('diagram_data', {}) # Default to empty JSON object

    try:
        user_id = db_ops._get_user_id_from_session(session)
        check_project_access(project_id, user_id, require_edit=True) # Must have edit rights to create

        query = """
            INSERT INTO diagrams (diagram_name, project_id, diagram_data)
            VALUES (%s, %s, %s::jsonb)
            RETURNING diagram_id, diagram_name, project_id, created_at, updated_at;
        """
        # diagram_data should be a string if your DB driver expects JSON string, 
        # or a dict if it handles dict-to-JSONB conversion (psycopg2 does for jsonb)
        import json
        diagram = db_ops._execute(query, (diagram_name, project_id, json.dumps(diagram_data)), fetchone=True, commit=True)
        return jsonify(diagram), 201
    except PermissionError as e:
        # Distinguish between auth error and project access error
        if "User not authenticated" in str(e) or "invalid session" in str(e):
             return jsonify(error=str(e)), 401
        elif "Project not found" in str(e):
            return jsonify(error=str(e)), 404
        else: # Other permission errors (access denied to project)
            return jsonify(error=str(e)), 403
    except Exception as e:
        return jsonify(error=f"Failed to create diagram: {str(e)}"), 500

@diagrams_bp.route('/projects/<int:project_id>/diagrams', methods=['GET'])
@login_required
def get_diagrams_for_project(project_id):
    try:
        user_id = db_ops._get_user_id_from_session(session)
        check_project_access(project_id, user_id) # Must have at least view rights

        query = "SELECT * FROM diagrams WHERE project_id = %s;"
        diagrams = db_ops._execute(query, (project_id,), fetchall=True)
        return jsonify(diagrams), 200
    except PermissionError as e:
        if "User not authenticated" in str(e) or "invalid session" in str(e):
             return jsonify(error=str(e)), 401
        elif "Project not found" in str(e):
            return jsonify(error=str(e)), 404
        else:
            return jsonify(error=str(e)), 403
    except Exception as e:
        return jsonify(error=f"Failed to retrieve diagrams: {str(e)}"), 500

@diagrams_bp.route('/diagrams/<int:diagram_id>', methods=['GET'])
@login_required
def get_diagram(diagram_id):
    try:
        user_id = db_ops._get_user_id_from_session(session)
        
        # Get project_id from diagram, then check project access
        diagram_info = db_ops._execute("SELECT project_id FROM diagrams WHERE diagram_id = %s", (diagram_id,), fetchone=True)
        if not diagram_info:
            return jsonify(error="Diagram not found."), 404
        
        project_id = diagram_info['project_id']
        check_project_access(project_id, user_id) # Check view access for the parent project

        diagram = db_ops._execute("SELECT * FROM diagrams WHERE diagram_id = %s", (diagram_id,), fetchone=True)
        # Already checked if diagram exists, so this should always return data
        return jsonify(diagram), 200
    except PermissionError as e: # Catches session errors and access errors
        if "User not authenticated" in str(e) or "invalid session" in str(e):
             return jsonify(error=str(e)), 401
        elif "Project not found" in str(e): # This implies the diagram's project is gone, or bad ID
            return jsonify(error="Diagram's parent project not found."), 404 # Or 403 if it's an access issue
        else: # Other permission errors (access denied to project)
            return jsonify(error=str(e)), 403
    except Exception as e:
        return jsonify(error=f"Failed to retrieve diagram: {str(e)}"), 500

@diagrams_bp.route('/diagrams/<int:diagram_id>', methods=['PUT'])
@login_required
def update_diagram(diagram_id):
    data = request.get_json()
    if not data:
        return jsonify(error="No data provided for update."), 400
    
    diagram_name = data.get('diagram_name')
    diagram_data = data.get('diagram_data')

    if not diagram_name and diagram_data is None: # Nothing to update
        return jsonify(error="Diagram name or data is required for update."), 400

    try:
        user_id = db_ops._get_user_id_from_session(session)

        # Get project_id from diagram, then check project access with edit rights
        diagram_info = db_ops._execute("SELECT project_id FROM diagrams WHERE diagram_id = %s", (diagram_id,), fetchone=True)
        if not diagram_info:
            return jsonify(error="Diagram not found."), 404
        
        project_id = diagram_info['project_id']
        check_project_access(project_id, user_id, require_edit=True)

        # Build query dynamically based on what's provided
        fields_to_update = []
        params = []
        if diagram_name:
            fields_to_update.append("diagram_name = %s")
            params.append(diagram_name)
        if diagram_data is not None:
            fields_to_update.append("diagram_data = %s::jsonb")
            import json
            params.append(json.dumps(diagram_data))
        
        if not fields_to_update: # Should be caught by earlier check, but as a safeguard
            return jsonify(error="No valid fields to update."), 400

        params.append(diagram_id) # For WHERE clause
        query = f"""
            UPDATE diagrams SET {', '.join(fields_to_update)}, updated_at = CURRENT_TIMESTAMP
            WHERE diagram_id = %s
            RETURNING *;
        """
        updated_diagram = db_ops._execute(query, tuple(params), fetchone=True, commit=True)
        return jsonify(updated_diagram), 200
    except PermissionError as e:
        if "User not authenticated" in str(e) or "invalid session" in str(e):
             return jsonify(error=str(e)), 401
        elif "Project not found" in str(e):
            return jsonify(error="Diagram's parent project not found."), 404
        else:
            return jsonify(error=str(e)), 403
    except Exception as e:
        return jsonify(error=f"Failed to update diagram: {str(e)}"), 500

@diagrams_bp.route('/diagrams/<int:diagram_id>', methods=['DELETE'])
@login_required
def delete_diagram(diagram_id):
    try:
        user_id = db_ops._get_user_id_from_session(session)

        diagram_info = db_ops._execute("SELECT project_id FROM diagrams WHERE diagram_id = %s", (diagram_id,), fetchone=True)
        if not diagram_info:
            return jsonify(error="Diagram not found."), 404
        
        project_id = diagram_info['project_id']
        check_project_access(project_id, user_id, require_edit=True) # Must have edit rights to delete

        db_ops._execute("DELETE FROM diagrams WHERE diagram_id = %s", (diagram_id,), commit=True)
        return jsonify(message="Diagram deleted successfully."), 200
    except PermissionError as e:
        if "User not authenticated" in str(e) or "invalid session" in str(e):
             return jsonify(error=str(e)), 401
        elif "Project not found" in str(e):
             return jsonify(error="Diagram's parent project not found."), 404
        else:
            return jsonify(error=str(e)), 403
    except Exception as e:
        return jsonify(error=f"Failed to delete diagram: {str(e)}"), 500
