// Base URL for the backend API
// const API_BASE_URL = 'http://localhost:5000/api'; // Adjust if your backend runs elsewhere

// --- User Authentication ---

async function checkUserStatus() {
    // Placeholder: In a real app, this would hit a backend endpoint like /api/profile
    // to get current user session information.
    try {
        const response = await fetch('/profile'); // Uses backend.app.profile route
        if (response.ok) {
            const data = await response.json();
            return data.user; // { user_id, email, name, ... }
        }
        if (response.status === 401) { // Unauthorized
            return null;
        }
        // For other errors, log them or handle appropriately
        console.error('Error checking user status:', response.statusText);
        return null;
    } catch (error) {
        console.error('Network error checking user status:', error);
        return null; // Assume logged out on network error
    }
}

// --- Projects API ---

async function getProjects() {
    // Placeholder: Simulates fetching projects
    console.log('API: Fetching projects...');
    // In a real app, this would be:
    // const response = await fetch(`${API_BASE_URL}/projects`);
    // if (!response.ok) throw new Error('Failed to fetch projects');
    // return await response.json();
    await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
    return [
        { project_id: 1, project_name: 'My First Project', user_id: 1, role: 'owner', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
        { project_id: 2, project_name: 'Shared Project Alpha', user_id: 2, role: 'edit', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
        { project_id: 3, project_name: 'Another Cool Project', user_id: 1, role: 'owner', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ];
}

async function createProject(projectName) {
    console.log(`API: Creating project "${projectName}"...`);
    // const response = await fetch(`${API_BASE_URL}/projects`, {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({ project_name: projectName })
    // });
    // if (!response.ok) throw new Error('Failed to create project');
    // return await response.json();
    await new Promise(resolve => setTimeout(resolve, 500));
    return { project_id: Date.now(), project_name: projectName, user_id: 1, role: 'owner', created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
}

async function getProjectDetails(projectId) {
    console.log(`API: Fetching details for project ${projectId}...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    return { project_id: projectId, project_name: `Project ${projectId} Details`, user_id: 1, created_at: new Date().toISOString() };
}

async function updateProject(projectId, newName) {
    console.log(`API: Updating project ${projectId} to "${newName}"...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    return { project_id: projectId, project_name: newName, user_id: 1, updated_at: new Date().toISOString() };
}

async function deleteProject(projectId) {
    console.log(`API: Deleting project ${projectId}...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    return { message: `Project ${projectId} deleted successfully` };
}


// --- Diagrams API ---

async function getDiagramsForProject(projectId) {
    console.log(`API: Fetching diagrams for project ${projectId}...`);
    await new Promise(resolve => setTimeout(resolve, 500));
    return [
        { diagram_id: 101, diagram_name: `Diagram A for Project ${projectId}`, project_id: projectId, created_at: new Date().toISOString() },
        { diagram_id: 102, diagram_name: `Diagram B for Project ${projectId}`, project_id: projectId, created_at: new Date().toISOString() },
    ];
}

async function createDiagram(projectId, diagramName, diagramData = {}) {
    console.log(`API: Creating diagram "${diagramName}" in project ${projectId}...`);
    await new Promise(resolve => setTimeout(resolve, 500));
    return { diagram_id: Date.now(), diagram_name: diagramName, project_id: projectId, diagram_data: diagramData, created_at: new Date().toISOString() };
}

async function getDiagramDetails(diagramId) {
    console.log(`API: Fetching details for diagram ${diagramId}...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    // Example: graph TD; A-->B;
    return { diagram_id: diagramId, diagram_name: `Diagram ${diagramId}`, project_id: 1, diagram_data: { code: `graph LR;\n  P${diagramId}Start --> P${diagramId}End;` }, updated_at: new Date().toISOString() };
}

async function updateDiagram(diagramId, diagramName, diagramData) {
    console.log(`API: Updating diagram ${diagramId} with name "${diagramName}"...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    return { diagram_id: diagramId, diagram_name: diagramName, diagram_data: diagramData, updated_at: new Date().toISOString() };
}

async function deleteDiagram(diagramId) {
    console.log(`API: Deleting diagram ${diagramId}...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    return { message: `Diagram ${diagramId} deleted successfully` };
}

// --- Sharing API ---
// Placeholder functions, to be implemented if sharing UI is built
async function getSharingPermissions(projectId) {
    console.log(`API: Getting sharing permissions for project ${projectId}...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    return [
        { user_id: 2, email: 'collaborator1@example.com', permission_level: 'edit' },
        { user_id: 3, email: 'collaborator2@example.com', permission_level: 'view' },
    ];
}

async function addCollaborator(projectId, email, permissionLevel) {
    console.log(`API: Adding ${email} as collaborator to project ${projectId} with ${permissionLevel} access...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    return { permission_id: Date.now(), project_id: projectId, user_id: Date.now(), email: email, permission_level: permissionLevel };
}

async function removeCollaborator(projectId, userId) {
    console.log(`API: Removing collaborator ${userId} from project ${projectId}...`);
    await new Promise(resolve => setTimeout(resolve, 300));
    return { message: 'Collaborator removed' };
}


// Export functions if using modules (ES6 or CommonJS)
// For simple script include, they are globally available.
// Example ES6:
// export { getProjects, createProject, getDiagramsForProject, createDiagram, getDiagramDetails, updateDiagram };

// This file uses placeholder data as requested by the subtask.
// To connect to a live backend, replace mock promises with `fetch` calls to backend API endpoints.
// Ensure the backend is running and CORS is configured if on different origins.
const Api = {
    checkUserStatus,
    getProjects,
    createProject,
    getProjectDetails,
    updateProject,
    deleteProject,
    getDiagramsForProject,
    createDiagram,
    getDiagramDetails,
    updateDiagram,
    deleteDiagram,
    getSharingPermissions,
    addCollaborator,
    removeCollaborator
};
