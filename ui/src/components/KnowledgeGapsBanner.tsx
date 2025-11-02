import React from 'react';
import { AlertTriangle } from 'lucide-react';
import './KnowledgeGapsBanner.css';

interface KnowledgeGap {
  component: string;
  missing_information: string;
  required_action: string;
  estimated_impact: string;
}

interface KnowledgeGapsBannerProps {
  gaps: KnowledgeGap[];
}

const KnowledgeGapsBanner: React.FC<KnowledgeGapsBannerProps> = ({ gaps }) => {
  if (!gaps || gaps.length === 0) {
    return null;
  }

  return (
    <div className="knowledge-gaps-banner">
      <div className="banner-header">
        <AlertTriangle size={20} className="warning-icon" />
        <h3 className="banner-title">⚠️ Knowledge Gaps Identified</h3>
      </div>
      <div className="gaps-list">
        {gaps.map((gap, index) => (
          <div key={index} className="gap-item">
            <div className="gap-header">
              <strong>{gap.component}:</strong> {gap.missing_information}
            </div>
            <div className="gap-details">
              <div className="required-action">
                <strong>Action:</strong> {gap.required_action}
              </div>
              <div className="estimated-impact">
                <strong>Impact:</strong>
                <span className={`impact-${gap.estimated_impact.toLowerCase()}`}>
                  {gap.estimated_impact}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KnowledgeGapsBanner;