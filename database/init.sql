-- Table for Users
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL, -- Name from Google, might not be unique if not primary handle
    email VARCHAR(255) UNIQUE NOT NULL,
    google_id VARCHAR(255) UNIQUE NULL, -- Google's unique user ID
    profile_pic_url VARCHAR(255) NULL, -- URL for user's profile picture
    password_hash VARCHAR(255) NULL, -- Password hash, nullable for OAuth users
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Optionally, add an updated_at field similar to other tables
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP 
);

-- It might be beneficial to also have an index on google_id if it's frequently used for lookups.
CREATE INDEX idx_users_google_id ON users(google_id);
-- Also, if username is still expected to be unique, it should remain UNIQUE.
-- If not, the UNIQUE constraint on username should be removed.
-- For now, I've removed UNIQUE from username and made it NOT NULL,
-- assuming google_id or email are the primary unique identifiers.
-- If username must be unique, it should be: username VARCHAR(255) UNIQUE NOT NULL,

-- Table for Projects
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Table for Diagrams
CREATE TABLE diagrams (
    diagram_id SERIAL PRIMARY KEY,
    diagram_name VARCHAR(255) NOT NULL,
    project_id INT NOT NULL,
    diagram_data JSONB, -- Using JSONB for potentially complex diagram data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- Table for Sharing Permissions
CREATE TABLE sharing_permissions (
    permission_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL,
    user_id INT NOT NULL,
    permission_level VARCHAR(50) NOT NULL, -- e.g., 'view', 'edit', 'admin'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (project_id, user_id) -- Ensures a user doesn't have multiple permissions for the same project
);

-- Indexes for faster lookups
CREATE INDEX idx_users_email ON users(email); -- Email is already unique, but an explicit index can be good
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_diagrams_project_id ON diagrams(project_id);
CREATE INDEX idx_sharing_project_id ON sharing_permissions(project_id);
CREATE INDEX idx_sharing_user_id ON sharing_permissions(user_id);

-- Optional: Add a trigger to update 'updated_at' timestamp on projects, diagrams, and users
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_diagrams_updated_at
BEFORE UPDATE ON diagrams
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
