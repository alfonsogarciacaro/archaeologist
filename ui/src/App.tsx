import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { apiClient } from './utils/apiClient';
import LoginPage from './components/LoginPage';
import Header from './components/Header';
import DependencyGraph from './components/DependencyGraph';
import InvestigationPanel from './components/InvestigationPanel';
import ExplanationPanel from './components/ExplanationPanel';
import KnowledgeGapsBanner from './components/KnowledgeGapsBanner';
import ProjectList from './components/ProjectList';
import FileUpload from './components/FileUpload';
import { ImpactReport } from './types/types';
import './App.css';
import './index.css';

export interface ProjectSource {
  id: number;
  original_filename: string;
  file_size: number;
  content_type: string;
  metadata?: string;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  repository_paths: string[] | null;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [currentView, setCurrentView] = useState<'projects' | 'investigation'>('projects');
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [impactReport, setImpactReport] = useState<ImpactReport | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [projectSources, setProjectSources] = useState<ProjectSource[]>([]);

  const handleInvestigate = async (query: string) => {
    setIsLoading(true);
    setSelectedNode(null);
    
    try {
      const report = await apiClient.investigate(query);
      setImpactReport(report);
    } catch (error) {
      console.error('Error during investigation:', error);
      // TODO: Show error message to user
    } finally {
      setIsLoading(false);
    }
  };

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId);
  };

  const selectedNodeData = impactReport?.nodes.find(node => node.id === selectedNode);

  const fetchProjectSources = async () => {
    if (!currentProject) return;

    try {
      const sources = await apiClient.getProjectSources(currentProject.id);
      setProjectSources(sources);
    } catch (error) {
      console.error('Error fetching project sources:', error);
    }
  };

  const handleFilesUploaded = () => {
    setShowFileUpload(false);
    // Refresh the project sources after upload
    fetchProjectSources();
  };

  const handleFileUploadClose = () => {
    setShowFileUpload(false);
  };

  // Fetch project sources when the current project changes
  useEffect(() => {
    if (currentProject && currentView === 'investigation') {
      fetchProjectSources();
    } else {
      setProjectSources([]);
    }
  }, [currentProject, currentView]);

  // Show loading screen while authentication is being initialized
  if (authLoading) {
    return (
      <div className="app loading-screen">
        <div className="loading-content">
          <h2>Initializing Enterprise Code Archaeologist...</h2>
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  // Show login screen if authentication failed and needs login
  // if (needsLogin) {
  //   return (
  //     <div className="app login-screen">
  //       <LoginPage />
  //     </div>
  //   );
  // }

  // Show loading screen while logging in
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="app loading-screen">
        <div className="loading-content">
          <h2>Initializing your secure session...</h2>
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  // Show project list when authenticated
  if (currentView === 'projects') {
    return (
      <div className="app projects-view">
        <ProjectList
          onOpenProject={(project) => {
            setCurrentProject(project);
            setCurrentView('investigation');
          }}
        />
      </div>
    );
  }

  return (
    <div className="app">
      <Header
        onInvestigate={handleInvestigate}
        isLoading={isLoading}
        onBackToProjects={() => setCurrentView('projects')}
        currentView={currentView}
        currentProject={currentProject}
      />
      
      {impactReport?.knowledge_gaps && impactReport.knowledge_gaps.length > 0 && (
        <KnowledgeGapsBanner gaps={impactReport.knowledge_gaps} />
      )}
      
      <div className="main-content">
        <div className="graph-container">
          <DependencyGraph
            report={impactReport}
            onNodeClick={handleNodeClick}
            selectedNodeId={selectedNode}
            projectSources={projectSources}
          />
        </div>
        
        {selectedNodeData && (
          <div className="sidebar">
            <InvestigationPanel node={selectedNodeData} />
          </div>
        )}
        
        {showExplanation && (
          <div className="explanation-sidebar">
            <ExplanationPanel explanation={impactReport?.explanation} />
          </div>
        )}
      </div>
      
      <div className="controls-bar">
        <button
          className="explanation-toggle"
          onClick={() => setShowExplanation(!showExplanation)}
        >
          {showExplanation ? 'Hide Explanation' : 'Show Explanation'}
        </button>

        <button
          className="upload-files-btn"
          onClick={() => setShowFileUpload(true)}
        >
          Upload Files
        </button>

        <div className="test-status-bar">
          Test Status: <span className="test-count">0 / 11 Tests Passing</span>
        </div>
      </div>

      {showFileUpload && currentProject && (
        <div className="modal-backdrop" onClick={(e) => {
          if (e.target === e.currentTarget) {
            handleFileUploadClose();
          }
        }}>
          <div className="modal-content">
            <FileUpload
              projectId={currentProject.id}
              onFilesUploaded={handleFilesUploaded}
              onClose={handleFileUploadClose}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;