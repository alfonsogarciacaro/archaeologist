import React from 'react';
import { ImpactReport } from '../types/types';
import './ExplanationPanel.css';

interface ExplanationPanelProps {
  explanation?: {
    reasoning_steps: string[];
    evidence_sources: Array<{
      file: string;
      line: number;
      content: string;
      confidence: number;
    }>;
    confidence_score?: number;
    analysis_type?: string;
  };
}

const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => {
  if (!explanation) {
      return (
          <div className="explanation-panel empty">
        <div className="panel-header">
          <h3>How We Reached This Conclusion</h3>
        </div>
        <div className="panel-content">
          <p>No explanation available</p>
        </div>
      </div>
    );
}

  const confidence_score = explanation?.confidence_score ?? 0;
  const analysis_type = explanation?.analysis_type ?? 'N/A';
  return (
    <div className="explanation-panel">
      <div className="panel-header">
        <h3>How We Reached This Conclusion</h3>
        <div className="confidence-indicator">
          <span className="confidence-label">Overall Confidence:</span>
          <div className="confidence-bar">
            <div 
              className="confidence-fill" 
              style={{ width: `${confidence_score * 100}%` }}
            />
          </div>
          <span className="confidence-value">{Math.round(confidence_score * 100)}%</span>
        </div>
      </div>
      
      <div className="panel-content">
        <div className="reasoning-section">
          <h4>Reasoning Steps</h4>
          <ol className="reasoning-steps">
            {explanation.reasoning_steps.map((step, index) => (
              <li key={index} className="reasoning-step">
                <span className="step-number">{index + 1}.</span>
                {step}
              </li>
            ))}
          </ol>
        </div>
        
        <div className="evidence-section">
          <h4>Evidence Sources</h4>
          <div className="evidence-grid">
            {explanation.evidence_sources.map((source, index) => (
              <div key={index} className="evidence-card">
                <div className="evidence-header">
                  <div className="evidence-file">
                    <span className="file-icon">📄</span>
                    <span className="file-name">{source.file.split('/').pop()}</span>
                  </div>
                  <div className="evidence-confidence">
                    <span className="confidence-badge">Confidence: {Math.round(source.confidence * 100)}%</span>
                  </div>
                </div>
                <div className="evidence-content">
                  <div className="code-snippet">
                    <pre>
                      <code>{source.content}</code>
                    </pre>
                  </div>
                  <div className="evidence-meta">
                    <span className="line-number">Line {source.line}</span>
                    {source.file.endsWith('.sql') && (
                      <span className="file-type">SQL</span>
                    )}
                    {source.file.endsWith('.py') && (
                      <span className="file-type">Python</span>
                    )}
                    {source.file.endsWith('.js') && (
                      <span className="file-type">JavaScript</span>
                    )}
                    {source.file.endsWith('.vba') && (
                      <span className="file-type">VBA</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="analysis-summary">
          <h4>Analysis Summary</h4>
          <div className="summary-grid">
            <div className="summary-item">
              <span className="summary-label">Analysis Type:</span>
              <span className="summary-value">{analysis_type}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Total Evidence:</span>
              <span className="summary-value">{explanation.evidence_sources.length} sources</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">High Confidence:</span>
              <span className="summary-value">
                {explanation.evidence_sources.filter(s => s.confidence > 0.8).length} sources
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExplanationPanel;