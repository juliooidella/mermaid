from flask_sockets import Sockets
import json # Using json for message structure

# Initialize Flask-Sockets
sockets = Sockets()

# Dictionary to store clients connected to each diagram.
# Structure: { diagram_id_1: {client_ws_1, client_ws_2}, diagram_id_2: {client_ws_3} }
# Using a set for clients to automatically handle duplicates and efficient removal.
diagram_clients = {}

@sockets.route('/ws/diagram/<int:diagram_id>')
def diagram_socket(ws, diagram_id):
    """Handles WebSocket connections for a specific diagram."""
    # Check if user is authenticated via session (optional but good practice)
    # from flask import session # Would need app context or pass session
    # user = session.get('user')
    # if not user:
    #     ws.close(message="User not authenticated.")
    #     return

    print(f"Client connected to diagram {diagram_id}, ws: {ws}")
    
    # Add client to the set for this diagram_id
    if diagram_id not in diagram_clients:
        diagram_clients[diagram_id] = set()
    diagram_clients[diagram_id].add(ws)

    try:
        while not ws.closed:
            # Receive message from client
            message = ws.receive()
            if message is None:  # Connection closed by client
                print(f"Client sent None, closing connection for diagram {diagram_id}, ws: {ws}")
                break 
            
            print(f"Message received for diagram {diagram_id} from {ws}: {message}")

            # For this basic implementation, we expect the message to be the Mermaid code string.
            # In a more advanced setup, messages might be JSON objects with type, payload, sender_id, etc.
            # e.g., data = json.loads(message)
            # mermaid_code = data.get('code')
            # sender_id = data.get('sender_id') # Could be user_id or a unique ws id

            # Broadcast the received message to all *other* clients in the same diagram room
            current_diagram_room = diagram_clients.get(diagram_id, set())
            for client_ws in list(current_diagram_room): # Iterate over a copy for safe removal
                if client_ws != ws and not client_ws.closed:
                    try:
                        # Send the raw message received. If using JSON, send json.dumps(data)
                        client_ws.send(message) 
                        print(f"Message sent to client {client_ws} in diagram {diagram_id}")
                    except Exception as e:
                        print(f"Error sending message to client {client_ws} in diagram {diagram_id}: {e}. Removing client.")
                        # If sending fails, assume client is disconnected and remove them
                        diagram_clients[diagram_id].remove(client_ws)
                        # ws.close() is handled by the client or gevent-websocket's internals mostly
                elif client_ws.closed: # Clean up already closed sockets
                    print(f"Removing already closed client {client_ws} from diagram {diagram_id}")
                    if client_ws in diagram_clients.get(diagram_id, set()):
                         diagram_clients[diagram_id].remove(client_ws)


    except Exception as e:
        # Log any errors that occur during the WebSocket handling
        print(f"Error in WebSocket handler for diagram {diagram_id}, ws {ws}: {e}")
    finally:
        # Ensure client is removed from the set when connection is closed or an error occurs
        print(f"Client disconnected from diagram {diagram_id}, ws: {ws}. Removing from clients list.")
        if diagram_id in diagram_clients and ws in diagram_clients[diagram_id]:
            diagram_clients[diagram_id].remove(ws)
            if not diagram_clients[diagram_id]: # If room is empty, delete it
                del diagram_clients[diagram_id]
        print(f"Current clients for diagram {diagram_id}: {diagram_clients.get(diagram_id)}")
