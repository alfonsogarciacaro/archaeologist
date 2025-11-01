import React from 'react';
import { X, Calendar, MapPin, BarChart } from 'lucide-react';
import { DependencyNode } from '../types/types';
import './InvestigationPanel.css';

interface InvestigationPanelProps {
  node: DependencyNode;
}

const InvestigationPanel: React.FC<InvestigationPanelProps> = ({ node }) => {
  const getSourceTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      live_repo: 'Live Repository',
      snapshot: 'Snapshot',
    };
    return labels[type] || type;
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      db_table: 'Database Table',
      repo: 'Repository',
      file: 'File',
      api_endpoint: 'API Endpoint',
    };
    return labels[type] || type;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#27ae60';
    if (confidence >= 0.6) return '#f39c12';
    return '#e74c3c';
  };

  const mockCodeSnippet = `// Found ${node.type} "${node.name}"
// Path: ${node.path}
// Source Type: ${node.source_type}
// Confidence: ${Math.round(node.confidence * 100)}%

// Example dependency found:
if (term_sheet_id) {
  // Process term sheet with legacy string ID
  processTermSheet(term_sheet_id);
}`;

  return (
    <div className="investigation-panel">
      <div className="panel-header">
        <h3 className="panel-title">Investigation Details</h3>
        <button className="close-button" onClick={() => window.history.back()}>
          <X size={16} />
        </button>
      </div>

      <div className="panel-content">
        <div className="node-info">
          <div className="node-header">
            <div className="node-name">{node.name}</div>
            <div className="node-type">{getTypeLabel(node.type)}</div>
          </div>

          <div className="node-details">
            <div className="detail-row">
              <MapPin size={14} className="detail-icon" />
              <span className="detail-label">Path:</span>
              <span className="detail-value">{node.path}</span>
            </div>

            <div className="detail-row">
              <BarChart size={14} className="detail-icon" />
              <span className="detail-label">Type:</span>
              <span className="detail-value">{getSourceTypeLabel(node.source_type)}</span>
            </div>

            <div className="detail-row">
              <span className="detail-label">Confidence:</span>
              <div className="confidence-bar">
                <div
                  className="confidence-fill"
                  style={{
                    width: `${node.confidence * 100}%`,
                    backgroundColor: getConfidenceColor(node.confidence),
                  }}
                />
                <span className="confidence-text">{Math.round(node.confidence * 100)}%</span>
              </div>
            </div>

            {node.last_updated && (
              <div className="detail-row">
                <Calendar size={14} className="detail-icon" />
                <span className="detail-label">Last Updated:</span>
                <span className="detail-value">{node.last_updated}</span>
              </div>
            )}
          </div>
        </div>

        <div className="code-evidence">
          <h4 className="section-title">Evidence Found</h4>
          <div className="code-snippet">
            <pre>{mockCodeSnippet}</pre>
          </div>
        </div>

        <div className="impact-assessment">
          <h4 className="section-title">Impact Assessment</h4>
          <div className="impact-content">
            <p>
              This <strong>{node.type}</strong> contains references that may be affected 
              by the proposed change. The <strong>{node.confidence >= 0.8 ? 'high' : node.confidence >= 0.6 ? 'medium' : 'low'}</strong> confidence 
              level suggests {node.confidence >= 0.8 ? 'strong evidence of dependency' : node.confidence >= 0.6 ? 'probable dependency' : 'potential dependency'}.
            </p>
            {node.source_type === 'snapshot' && (
              <p className="snapshot-warning">
                <strong>Note:</strong> This is a snapshot source. Changes in the live system 
                may not be reflected here.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvestigationPanel;