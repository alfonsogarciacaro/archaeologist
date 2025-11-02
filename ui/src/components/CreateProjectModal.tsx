import React, { useState } from 'react';
import { apiClient } from '../utils/apiClient';
import './CreateProjectModal.css';

interface CreateProjectModalProps {
  onClose: () => void;
  onProjectCreated: () => void;
}

const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  onClose,
  onProjectCreated,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);

  const validateName = async (value: string) => {
    if (!value.trim()) {
      setNameError('Project name is required');
      return false;
    }
    
    if (value.trim().length < 2) {
      setNameError('Project name must be at least 2 characters');
      return false;
    }
    
    if (value.trim().length > 100) {
      setNameError('Project name must be less than 100 characters');
      return false;
    }

    // Check for unique name
    try {
      const projects = await apiClient.getProjects();
      const existingProject = projects.find((p: any) => 
        p.name.toLowerCase() === value.trim().toLowerCase()
      );
      
      if (existingProject) {
        setNameError('A project with this name already exists');
        return false;
      }
      
      setNameError(null);
      return true;
    } catch (err) {
      console.error('Error checking project name uniqueness:', err);
      // Continue with validation even if we can't check uniqueness
      setNameError(null);
      return true;
    }
  };

  const handleNameChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setName(value);
    
    if (value.trim()) {
      await validateName(value);
    } else {
      setNameError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate name
    const isNameValid = await validateName(name);
    if (!isNameValid) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const projectData = {
        name: name.trim(),
        description: description.trim() || null,
        repository_paths: [], // Start with empty repository paths
      };

      await apiClient.createProject(projectData);
      onProjectCreated();
    } catch (err: any) {
      console.error('Failed to create project:', err);
      if (err.message?.includes('already exists')) {
        setNameError('A project with this name already exists');
      } else {
        setError(err.message || 'Failed to create project. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content">
        <div className="modal-header">
          <h2>Create New Project</h2>
          <button className="close-btn" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="project-form">
          <div className="form-group">
            <label htmlFor="project-name">
              Project Name <span className="required">*</span>
            </label>
            <input
              id="project-name"
              type="text"
              value={name}
              onChange={handleNameChange}
              placeholder="Enter project name"
              maxLength={100}
              required
              disabled={loading}
              className={nameError ? 'error' : ''}
            />
            {nameError && <span className="error-text">{nameError}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="project-description">
              Description <span className="optional">(optional)</span>
            </label>
            <textarea
              id="project-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your project's purpose or scope"
              maxLength={500}
              rows={4}
              disabled={loading}
            />
            <div className="char-count">
              {description.length}/500 characters
            </div>
          </div>

          {error && (
            <div className="form-error">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="form-actions">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="cancel-btn"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim() || !!nameError}
              className="submit-btn"
            >
              {loading ? (
                <>
                  <div className="btn-spinner"></div>
                  Creating Project...
                </>
              ) : (
                'Create Project'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProjectModal;