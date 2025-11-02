import React, { useState, useEffect } from 'react';
import { apiClient } from '../utils/apiClient';
import { useAuth } from '../contexts/AuthContext';
import CreateProjectModal from './CreateProjectModal';
import { Project } from '../App';
import './ProjectList.css';

interface ProjectListProps {
  onOpenProject: (project: Project) => void;
}

const ProjectList: React.FC<ProjectListProps> = ({ onOpenProject }) => {
  const { user } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const projectsData = await apiClient.getProjects();
      setProjects(projectsData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch projects:', err);
      setError('Failed to load projects. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchProjects();
    }
  }, [user]);

  const handleProjectCreated = () => {
    setShowCreateModal(false);
    fetchProjects(); // Refresh the project list
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="project-list loading">
        <div className="loading-spinner"></div>
        <h3>Loading your projects...</h3>
      </div>
    );
  }

  if (error) {
    return (
      <div className="project-list error">
        <div className="error-message">
          <h3>⚠️ {error}</h3>
          <button onClick={fetchProjects} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="project-list">
      <div className="project-list-header">
        <h2>Your Projects</h2>
        <button
          className="create-project-btn"
          onClick={() => setShowCreateModal(true)}
        >
          <span className="btn-icon">+</span>
          New Project
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="empty-state">
          <h3>No projects yet</h3>
          <p>Create your first project to start investigating code dependencies.</p>
          <button
            className="create-first-project-btn"
            onClick={() => setShowCreateModal(true)}
          >
            Create Your First Project
          </button>
        </div>
      ) : (
        <div className="projects-grid">
          {projects.map((project) => (
            <div key={project.id} className="project-card">
              <div className="project-header">
                <h3 className="project-name">{project.name}</h3>
                <span className={`project-status ${project.is_active ? 'active' : 'inactive'}`}>
                  {project.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              
              {project.description && (
                <p className="project-description">{project.description}</p>
              )}
              
              <div className="project-meta">
                <div className="project-paths">
                  {project.repository_paths && project.repository_paths.length > 0 ? (
                    <span className="path-count">
                      {project.repository_paths.length} repository{project.repository_paths.length !== 1 ? 'ies' : 'y'}
                    </span>
                  ) : (
                    <span className="no-paths">No repositories configured</span>
                  )}
                </div>
                
                <div className="project-dates">
                  <span className="created-date">
                    Created {formatDate(project.created_at)}
                  </span>
                  {project.updated_at !== project.created_at && (
                    <span className="updated-date">
                      Updated {formatDate(project.updated_at)}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="project-actions">
                <button className="open-project-btn" onClick={() => onOpenProject(project)}>
                  Open Project
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreateModal && (
        <CreateProjectModal
          onClose={() => setShowCreateModal(false)}
          onProjectCreated={handleProjectCreated}
        />
      )}
    </div>
  );
};

export default ProjectList;