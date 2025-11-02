import React, { useState } from 'react';
import Header from './components/Header';
import DependencyGraph from './components/DependencyGraph';
import InvestigationPanel from './components/InvestigationPanel';
import ExplanationPanel from './components/ExplanationPanel';
import KnowledgeGapsBanner from './components/KnowledgeGapsBanner';
import { ImpactReport } from './types/types';
import './App.css';
import './index.css';

const App: React.FC = () => {
  const [impactReport, setImpactReport] = useState<ImpactReport | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  const handleInvestigate = async (query: string) => {
    setIsLoading(true);
    setSelectedNode(null);
    
    try {
      const response = await fetch('/api/v1/investigate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      
      if (!response.ok) {
        throw new Error('Investigation failed');
      }
      
      const report: ImpactReport = await response.json();
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

export default App;