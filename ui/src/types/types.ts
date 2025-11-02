export interface DependencyNode {
  id: string;
  name: string;
  type: string;
  path: string;
  source_type: string;
  confidence: number;
  last_updated?: string;
}

export interface DependencyEdge {
  source: string;
  target: string;
  confidence: number;
  relationship_type: string;
  evidence: string;
}

export interface KnowledgeGap {
  component: string;
  missing_information: string;
  required_action: string;
  estimated_impact: string;
}

export interface ImpactReport {
  query: string;
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  knowledge_gaps: KnowledgeGap[];
  summary: string;
  explanation?: {
    reasoning_steps: string[];
    evidence_sources: Array<{
      file: string;
      line: number;
      content: string;
      confidence: number;
    }>;
    confidence_score: number;
    analysis_type: string;
  };
  recommendations?: string[];
}