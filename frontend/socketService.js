const SocketService = {
    connect(diagramId, onMessageCallback, onErrorCallback, onCloseCallback) {
        // Determine WebSocket protocol (ws or wss)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Use window.location.host to get the hostname and port
        const host = window.location.host;
        const socketUrl = `${protocol}//${host}/ws/diagram/${diagramId}`;

        console.log(`SocketService: Connecting to ${socketUrl}`);
        const socket = new WebSocket(socketUrl);

        socket.onopen = () => {
            console.log(`SocketService: WebSocket connection established for diagram ${diagramId}.`);
        };

        socket.onmessage = (event) => {
            console.log(`SocketService: Message received for diagram ${diagramId}:`, event.data);
            if (onMessageCallback) {
                onMessageCallback(event.data);
            }
        };

        socket.onerror = (error) => {
            console.error(`SocketService: WebSocket error for diagram ${diagramId}:`, error);
            if (onErrorCallback) {
                onErrorCallback(error);
            }
        };

        socket.onclose = (event) => {
            console.log(`SocketService: WebSocket connection closed for diagram ${diagramId}. Code: ${event.code}, Reason: ${event.reason}`);
            if (onCloseCallback) {
                onCloseCallback(event);
            }
        };

        return socket;
    },

    send(socket, message) {
        if (socket && socket.readyState === WebSocket.OPEN) {
            console.log("SocketService: Sending message:", message);
            socket.send(message);
        } else {
            console.error("SocketService: WebSocket is not open. Cannot send message.");
        }
    },

    close(socket) {
        if (socket) {
            console.log("SocketService: Closing WebSocket connection.");
            socket.close();
        }
    }
};

// If using modules:
// export default SocketService;
