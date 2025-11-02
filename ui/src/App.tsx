import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { apiClient } from './utils/apiClient';
import LoginPage from './components/LoginPage';
import Header from './components/Header';
import DependencyGraph from './components/DependencyGraph';
import InvestigationPanel from './components/InvestigationPanel';
import ExplanationPanel from './components/ExplanationPanel';
import KnowledgeGapsBanner from './components/KnowledgeGapsBanner';
import { ImpactReport } from './types/types';
import './App.css';
import './index.css';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, needsLogin } = useAuth();
  const [impactReport, setImpactReport] = useState<ImpactReport | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

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
  if (needsLogin) {
    return (
      <div className="app login-screen">
        <LoginPage />
      </div>
    );
  }

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

  return (
    <div className="app">
      <Header onInvestigate={handleInvestigate} isLoading={isLoading} />
      
      {impactReport?.knowledge_gaps && impactReport.knowledge_gaps.length > 0 && (
        <KnowledgeGapsBanner gaps={impactReport.knowledge_gaps} />
      )}
      
      <div className="main-content">
        <div className="graph-container">
          <DependencyGraph
            report={impactReport}
            onNodeClick={handleNodeClick}
            selectedNodeId={selectedNode}
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
        
        <div className="test-status-bar">
          Test Status: <span className="test-count">0 / 11 Tests Passing</span>
        </div>
      </div>
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