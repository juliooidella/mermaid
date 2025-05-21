// DOM Element Selectors
const views = {
    welcome: document.getElementById('welcome-view'),
    projects: document.getElementById('projects-view'),
    diagrams: document.getElementById('diagrams-view'),
    editor: document.getElementById('editor-view'),
};

const projectList = document.getElementById('project-list');
const diagramList = document.getElementById('diagram-list');
const projectNameHeader = document.getElementById('project-name-header').querySelector('span');
const diagramNameHeader = document.getElementById('diagram-name-header').querySelector('span');
const mermaidCodeTextarea = document.getElementById('mermaid-code');
const mermaidOutputDiv = document.getElementById('mermaid-output');

const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const userInfoDiv = document.getElementById('user-info');
const usernameDisplay = document.getElementById('username-display');


// --- View Management ---
function showView(viewId) {
    for (const id in views) {
        if (views[id]) { // Check if element exists
            views[id].style.display = (id === viewId) ? 'block' : 'none';
        } else {
            console.warn(`UI: View element with id '${id}-view' not found.`);
        }
    }
    console.log(`UI: Switched to ${viewId} view`);
}

// --- User Authentication UI ---
function updateUserAuthUI(user) {
    if (user) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'block';
        userInfoDiv.style.display = 'block';
        usernameDisplay.textContent = user.name || user.email;
    } else {
        loginBtn.style.display = 'block';
        logoutBtn.style.display = 'none';
        userInfoDiv.style.display = 'none';
        usernameDisplay.textContent = '';
    }
}

// --- Project List UI ---
function renderProjectList(projects) {
    if (!projectList) {
        console.error("UI: Project list element not found.");
        return;
    }
    projectList.innerHTML = ''; // Clear existing list
    if (!projects || projects.length === 0) {
        projectList.innerHTML = '<li>No projects found.</li>';
        return;
    }
    projects.forEach(project => {
        const li = document.createElement('li');
        li.textContent = project.project_name;
        li.dataset.projectId = project.project_id; // Store project ID
        li.dataset.role = project.role; // Store role (owner, edit, view)
        
        // Add a delete button for owners
        if (project.role === 'owner') {
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.classList.add('delete-project-btn'); // For event delegation
            deleteBtn.style.marginLeft = '10px'; // Basic styling
            deleteBtn.onclick = (event) => {
                event.stopPropagation(); // Prevent li click event
                // Emit an event or call a handler function in app.js
                document.dispatchEvent(new CustomEvent('deleteProjectClicked', { detail: project.project_id }));
            };
            li.appendChild(deleteBtn);
        }
        
        projectList.appendChild(li);
    });
}

// --- Diagram List UI ---
function renderDiagramList(project, diagrams) {
    if (!diagramList || !projectNameHeader) {
        console.error("UI: Diagram list or project name header element not found.");
        return;
    }
    projectNameHeader.textContent = project.project_name;
    diagramList.innerHTML = ''; // Clear existing list
    if (!diagrams || diagrams.length === 0) {
        diagramList.innerHTML = '<li>No diagrams found in this project.</li>';
        return;
    }
    diagrams.forEach(diagram => {
        const li = document.createElement('li');
        li.textContent = diagram.diagram_name;
        li.dataset.diagramId = diagram.diagram_id; // Store diagram ID
        
        // Add a delete button (assuming project owner or diagram creator can delete)
        // More complex permission check might be needed based on project role
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.classList.add('delete-diagram-btn');
        deleteBtn.style.marginLeft = '10px';
        deleteBtn.onclick = (event) => {
            event.stopPropagation();
            document.dispatchEvent(new CustomEvent('deleteDiagramClicked', { detail: { projectId: project.project_id, diagramId: diagram.diagram_id } }));
        };
        li.appendChild(deleteBtn);

        diagramList.appendChild(li);
    });
}

// --- Editor UI ---
function populateEditor(diagram) {
    if (!diagramNameHeader || !mermaidCodeTextarea) {
        console.error("UI: Editor elements not found.");
        return;
    }
    diagramNameHeader.textContent = diagram.diagram_name;
    // Diagram data might be JSON string or object. Ensure it's parsed if necessary.
    let code = '';
    if (diagram.diagram_data && typeof diagram.diagram_data === 'object' && diagram.diagram_data.code) {
        code = diagram.diagram_data.code;
    } else if (typeof diagram.diagram_data === 'string') { // Fallback if it's just a string
        code = diagram.diagram_data;
    }
    mermaidCodeTextarea.value = code;
    renderMermaidDiagram(code); // Initial render
}

async function renderMermaidDiagram(code) {
    if (!mermaidOutputDiv) {
        console.error("UI: Mermaid output element not found.");
        return;
    }

    // Clear previous output
    mermaidOutputDiv.innerHTML = '';

    if (!code || code.trim() === "") {
        mermaidOutputDiv.innerHTML = "<p class='mermaid-placeholder'>Enter Mermaid code above to see the diagram.</p>";
        return;
    }

    // Optional: Add a loading indicator
    // mermaidOutputDiv.innerHTML = "<p class='mermaid-loading'>Rendering diagram...</p>";

    try {
        if (typeof mermaid === 'undefined') {
            console.error('Mermaid library is not loaded.');
            mermaidOutputDiv.innerHTML = "<p class='mermaid-error'>Error: Mermaid library not loaded.</p>";
            return;
        }

        // Generate a unique ID for each render to avoid conflicts if mermaid caches IDs internally
        const renderId = 'mermaid-graph-' + Date.now();
        const { svg, bindFunctions } = await mermaid.render(renderId, code);
        
        mermaidOutputDiv.innerHTML = svg; // Set the new SVG
        
        if (bindFunctions) {
            bindFunctions(mermaidOutputDiv); // Attach event listeners if any
        }
    } catch (error) {
        console.error("Mermaid rendering error:", error);
        // Improve error display
        const errorMessage = error.message || "Unknown rendering error.";
        // Sanitize errorMessage if it might contain HTML/script, though Mermaid errors are usually plain text.
        // For this context, assuming error.message is safe.
        mermaidOutputDiv.innerHTML = `
            <div class="mermaid-error">
                <strong>Error Rendering Diagram:</strong>
                <p>${errorMessage.replace(/\n/g, '<br>')}</p>
                <details>
                    <summary>Show problematic code</summary>
                    <pre>${code}</pre>
                </details>
            </div>`;
    }
}

// Expose UI functions
const UI = {
    showView,
    updateUserAuthUI,
    renderProjectList,
    renderDiagramList,
    populateEditor,
    renderMermaidDiagram,
    // Selectors that app.js might need for event listeners
    projectList,
    diagramList,
    mermaidCodeTextarea,
    // Potentially other elements if app.js needs direct access
};

// Note: This is a simple UI module. In a larger application,
// you might use classes or more structured components.
// Event listeners for buttons like "Create Project", "Save Diagram" etc.
// will be set up in app.js as they involve application logic and API calls.
