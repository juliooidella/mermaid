document.addEventListener('DOMContentLoaded', () => {
    // Initial state
    let currentUser = null;
    let currentProjects = [];
    let currentProject = null; // Selected project
    let currentDiagrams = [];
    let currentDiagram = null; // Selected diagram for editing
    let diagramSocket = null; // WebSocket for the current diagram
    let isRemoteUpdate = false; // Flag to prevent echo loops

    // --- DOM Elements from UI.js (or query them here if not exposed) ---
    const homeLink = document.getElementById('home-link');
    const projectsLink = document.getElementById('projects-link');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');

    const createProjectBtn = document.getElementById('create-project-btn');
    const backToProjectsBtn = document.getElementById('back-to-projects-btn');
    const createDiagramBtn = document.getElementById('create-diagram-btn');
    const backToDiagramsBtn = document.getElementById('back-to-diagrams-btn');
    const saveDiagramBtn = document.getElementById('save-diagram-btn');
    
    // --- Initialization ---
    async functioninitializeApp() {
        console.log("App: Initializing...");
        // Check user status on load
        currentUser = await Api.checkUserStatus();
        UI.updateUserAuthUI(currentUser);

        if (currentUser) {
            UI.showView('projects');
            await loadProjects();
        } else {
            UI.showView('welcome');
        }
        setupEventListeners();
    }

    // --- Event Listeners Setup ---
    function setupEventListeners() {
        loginBtn.addEventListener('click', handleLogin);
        logoutBtn.addEventListener('click', handleLogout);
        homeLink.addEventListener('click', (e) => { e.preventDefault(); navigateHome(); });
        projectsLink.addEventListener('click', (e) => { e.preventDefault(); if (currentUser) { UI.showView('projects'); loadProjects(); } else { UI.showView('welcome'); } });

        createProjectBtn.addEventListener('click', handleCreateProject);
        UI.projectList.addEventListener('click', handleProjectSelection); // Using UI.projectList for event delegation
        
        backToProjectsBtn.addEventListener('click', () => { UI.showView('projects'); currentProject = null; });
        createDiagramBtn.addEventListener('click', handleCreateDiagram);
        UI.diagramList.addEventListener('click', handleDiagramSelection); // Using UI.diagramList
        
        backToDiagramsBtn.addEventListener('click', () => { 
            if (currentProject) {
                UI.showView('diagrams'); 
                loadDiagrams(currentProject.project_id); // Reload diagrams for current project
            } else {
                UI.showView('projects'); // Fallback if no current project
            }
            currentDiagram = null;
            if (diagramSocket) {
                SocketService.close(diagramSocket);
                diagramSocket = null;
            }
        });
        saveDiagramBtn.addEventListener('click', handleSaveDiagram);
        UI.mermaidCodeTextarea.addEventListener('input', debounce(handleMermaidCodeChange, 500));

        // Listen for custom delete events from ui.js
        document.addEventListener('deleteProjectClicked', async (event) => {
            const projectId = event.detail;
            await handleDeleteProject(projectId);
        });
        document.addEventListener('deleteDiagramClicked', async (event) => {
            const { projectId, diagramId } = event.detail;
            await handleDeleteDiagram(projectId, diagramId);
        });
    }

    // --- Navigation & View Switching ---
    function navigateHome() {
        if (currentUser) {
            UI.showView('projects');
            loadProjects();
        } else {
            UI.showView('welcome');
        }
    }

    // --- Authentication ---
    function handleLogin() {
        console.log("App: Login clicked");
        window.location.href = '/login/google'; // Redirect to backend Google login route
    }

    async function handleLogout() {
        console.log("App: Logout clicked");
        // In a real app, call backend logout if necessary: await Api.logout();
        // For now, just clear session client-side for UI demo
        try {
            const response = await fetch('/logout'); // Call backend logout
            if (response.ok) {
                currentUser = null;
                UI.updateUserAuthUI(null);
                UI.showView('welcome');
                currentProjects = [];
                currentProject = null;
                currentDiagrams = [];
                currentDiagram = null;
                UI.renderProjectList([]); // Clear lists
                UI.renderDiagramList({project_name: ''}, []);
            } else {
                console.error("Logout failed on backend:", await response.text());
                alert("Logout failed. Please try again.");
            }
        } catch (error) {
            console.error("Error during logout:", error);
            alert("Error during logout. Please try again.");
        }
    }
    
    // --- Project Management ---
    async function loadProjects() {
        if (!currentUser) return;
        console.log("App: Loading projects...");
        try {
            currentProjects = await Api.getProjects();
            UI.renderProjectList(currentProjects);
        } catch (error) {
            console.error("App: Error loading projects:", error);
            UI.projectList.innerHTML = '<li>Error loading projects.</li>';
        }
    }

    async function handleCreateProject() {
        const projectName = prompt("Enter new project name:");
        if (projectName && projectName.trim() !== "") {
            try {
                const newProject = await Api.createProject(projectName.trim());
                currentProjects.push(newProject);
                UI.renderProjectList(currentProjects); // Re-render
            } catch (error) {
                console.error("App: Error creating project:", error);
                alert("Failed to create project.");
            }
        }
    }

    async function handleProjectSelection(event) {
        if (event.target.tagName === 'LI' || event.target.closest('li')) {
            const li = event.target.closest('li');
            const projectId = parseInt(li.dataset.projectId);
            if (!isNaN(projectId)) {
                currentProject = currentProjects.find(p => p.project_id === projectId);
                if (currentProject) {
                    console.log(`App: Project ${currentProject.project_name} selected.`);
                    UI.showView('diagrams');
                    await loadDiagrams(currentProject.project_id);
                }
            }
        }
    }
    
    async function handleDeleteProject(projectId) {
        if (!confirm("Are you sure you want to delete this project and all its diagrams?")) return;
        try {
            await Api.deleteProject(projectId);
            currentProjects = currentProjects.filter(p => p.project_id !== projectId);
            UI.renderProjectList(currentProjects);
            if (currentProject && currentProject.project_id === projectId) {
                currentProject = null;
                // Optionally switch to projects view if the active project was deleted
                UI.showView('projects');
            }
        } catch (error) {
            console.error("App: Error deleting project:", error);
            alert("Failed to delete project.");
        }
    }

    // --- Diagram Management ---
    async function loadDiagrams(projectId) {
        if (!currentProject) return;
        console.log(`App: Loading diagrams for project ${projectId}...`);
        try {
            currentDiagrams = await Api.getDiagramsForProject(projectId);
            UI.renderDiagramList(currentProject, currentDiagrams);
        } catch (error) {
            console.error("App: Error loading diagrams:", error);
            UI.diagramList.innerHTML = '<li>Error loading diagrams.</li>';
        }
    }

    async function handleCreateDiagram() {
        if (!currentProject) {
            alert("Please select a project first.");
            return;
        }
        const diagramName = prompt("Enter new diagram name:");
        if (diagramName && diagramName.trim() !== "") {
            try {
                // Default diagram data
                const defaultDiagramData = { code: `graph TD;\n  A[${diagramName}] --> B[Edit Me!];` };
                const newDiagram = await Api.createDiagram(currentProject.project_id, diagramName.trim(), defaultDiagramData);
                currentDiagrams.push(newDiagram);
                UI.renderDiagramList(currentProject, currentDiagrams); // Re-render
            } catch (error) {
                console.error("App: Error creating diagram:", error);
                alert("Failed to create diagram.");
            }
        }
    }

    async function handleDiagramSelection(event) {
        if (event.target.tagName === 'LI' || event.target.closest('li')) {
            const li = event.target.closest('li');
            const diagramId = parseInt(li.dataset.diagramId);
            if (!isNaN(diagramId)) {
                // Close previous socket if open
                if (diagramSocket) {
                    SocketService.close(diagramSocket);
                    diagramSocket = null;
                }

                currentDiagram = currentDiagrams.find(d => d.diagram_id === diagramId);
                if (currentDiagram) {
                    console.log(`App: Diagram ${currentDiagram.diagram_name} selected.`);
                    const detailedDiagram = await Api.getDiagramDetails(currentDiagram.diagram_id);
                    currentDiagram = detailedDiagram; 
                    UI.showView('editor');
                    UI.populateEditor(currentDiagram); // This will also do an initial render

                    // Establish WebSocket connection for the selected diagram
                    diagramSocket = SocketService.connect(
                        currentDiagram.diagram_id,
                        handleIncomingSocketMessage,
                        handleSocketError,
                        handleSocketClose
                    );
                }
            }
        }
    }

    async function handleDeleteDiagram(projectId, diagramId) {
        // projectId is available from the event detail if needed for context, 
        // but Api.deleteDiagram typically just needs diagramId
        if (!confirm("Are you sure you want to delete this diagram?")) return;
        try {
            await Api.deleteDiagram(diagramId);
            currentDiagrams = currentDiagrams.filter(d => d.diagram_id !== diagramId);
            UI.renderDiagramList(currentProject, currentDiagrams); // Re-render the list for the current project
            if (currentDiagram && currentDiagram.diagram_id === diagramId) {
                currentDiagram = null;
                // Optionally, switch to diagrams view if the active diagram was deleted
                UI.showView('diagrams');
            }
        } catch (error) {
            console.error("App: Error deleting diagram:", error);
            alert("Failed to delete diagram.");
        }
    }

    // --- Editor Logic ---
    async function handleSaveDiagram() {
        if (!currentDiagram) {
            alert("No diagram selected for saving.");
            return;
        }
        const newCode = UI.mermaidCodeTextarea.value;
        // Assuming diagram name isn't changed here, but could add UI for it
        const newName = currentDiagram.diagram_name; 
        
        // Structure for diagram_data might be just the code string, or an object like { code: "..." }
        // The backend API for diagrams (PUT /api/diagrams/<id>) expects `diagram_data`
        // Let's assume diagram_data is an object: { "code": "..." }
        const newDiagramData = { code: newCode };

        try {
            const updatedDiagram = await Api.updateDiagram(currentDiagram.diagram_id, newName, newDiagramData);
            currentDiagram = updatedDiagram; // Update local copy
            // Update in the list as well, if necessary (e.g. if name changed)
            const index = currentDiagrams.findIndex(d => d.diagram_id === currentDiagram.diagram_id);
            if (index !== -1) {
                currentDiagrams[index] = updatedDiagram;
            }
            alert("Diagram saved successfully!");
            // No need to re-render mermaid here, it's done on input change
        } catch (error) {
            console.error("App: Error saving diagram:", error);
            alert("Failed to save diagram.");
        }
    }

    function handleMermaidCodeChange() {
        if (isRemoteUpdate) { // If update came from socket, don't send it back
            isRemoteUpdate = false; // Reset flag
            return;
        }
        if (currentDiagram && diagramSocket) {
            const code = UI.mermaidCodeTextarea.value;
            UI.renderMermaidDiagram(code); // Render locally first
            SocketService.send(diagramSocket, code); // Send update to other clients
            console.log("App: Sent diagram update via WebSocket.");
        } else if (currentDiagram) { // Diagram loaded, but no socket (local editing only)
             const code = UI.mermaidCodeTextarea.value;
             UI.renderMermaidDiagram(code);
        }
    }

    // --- WebSocket Event Handlers ---
    function handleIncomingSocketMessage(newCode) {
        if (currentDiagram && UI.mermaidCodeTextarea.value !== newCode) {
            console.log("App: Received diagram update via WebSocket:", newCode.substring(0,50) + "...");
            isRemoteUpdate = true; // Set flag to prevent echo
            UI.mermaidCodeTextarea.value = newCode;
            UI.renderMermaidDiagram(newCode);
            // Update currentDiagram's data if needed, though saving is a separate step
            if (currentDiagram.diagram_data && typeof currentDiagram.diagram_data === 'object') {
                currentDiagram.diagram_data.code = newCode;
            } else {
                currentDiagram.diagram_data = { code: newCode };
            }
        }
    }

    function handleSocketError(error) {
        console.error("App: WebSocket connection error.", error);
        // Optionally, display a user-friendly message, e.g., using a toast notification
        alert("Real-time collaboration error: Connection to the server failed or was interrupted.");
        // You might want to disable collaborative features or attempt reconnection here.
        if (diagramSocket) {
            SocketService.close(diagramSocket); // Ensure it's fully closed
            diagramSocket = null;
        }
    }

    function handleSocketClose(event) {
        console.log("App: WebSocket connection closed.", event.reason ? `Reason: ${event.reason}` : `Code: ${event.code}`);
        // Optionally, inform the user if the closure was unexpected.
        // if (!event.wasClean) { // Check event.wasClean if available
        //     alert("Real-time collaboration session ended unexpectedly.");
        // }
        diagramSocket = null; // Clear the socket reference
    }


    // --- Utility ---
    function debounce(func, delay) {
        let timeout;
        return function(...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), delay);
        };
    }

    // --- Start the app ---
    initializeApp();
});
