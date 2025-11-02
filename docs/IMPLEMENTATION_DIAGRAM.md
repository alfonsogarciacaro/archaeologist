# Enterprise Code Archaeologist - Implementation Diagrams

## Current Architecture Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React UI]
    end
    
    subgraph "API Service (Orchestrator)"
        API[FastAPI Main]
        LLM[LLM Interface]
        MockLLM[Mock LLM Service]
    end
    
    subgraph "Scanner Service (Search Engine)"
        Scan[Literal Scanner]
        DepAnalysis[Dependency Analysis]
        ImpactAnalysis[Impact Analysis]
    end
    
    subgraph "Data Layer"
        VectorDB[Qdrant VectorDB]
        FileSystem[Mock Enterprise Data]
    end
    
    UI --> API
    API --> LLM
    API --> Scan
    LLM --> MockLLM
    Scan --> DepAnalysis
    DepAnalysis --> ImpactAnalysis
    Scan --> FileSystem
    VectorDB -.-> Scan
    
    style UI fill:#e1f5fe
    style API fill:#f3e5f5
    style Scan fill:#e8f5e8
    style VectorDB fill:#fff3e0
```

## Implementation Phase Flow

```mermaid
gantt
    title Enterprise Code Archaeologist Implementation Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1: Foundation
    Fix Core Integration    :p1-1, 2025-11-04, 2d
    Complete Mock LLM       :p1-2, after p1-1, 2d
    Enhance Scanner        :p1-3, after p1-2, 3d
    
    section Phase 2: Semantic Search
    Embedding Service       :p2-1, after p1-3, 3d
    Data Ingestion         :p2-2, after p2-1, 2d
    VectorDB Integration    :p2-3, after p2-2, 2d
    
    section Phase 3: LLM Intelligence
    Real LLM Integration   :p3-1, after p2-3, 3d
    Advanced Analysis       :p3-2, after p3-1, 2d
    Guardrail System       :p3-3, after p3-2, 2d
    
    section Phase 4: Production
    Performance Opt        :p4-1, after p3-3, 2d
    UI/UX Enhancements    :p4-2, after p4-1, 2d
    Production Deploy       :p4-3, after p4-2, 3d
```

## Target Architecture (End State)

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Dashboard]
        Graph[Dependency Graph]
        Panel[Investigation Panel]
        Banner[Knowledge Gaps Banner]
    end
    
    subgraph "API Service (Orchestrator)"
        API[FastAPI Router]
        Orchestrator[Investigation Orchestrator]
        RealLLM[Real LLM Service]
        Guardrails[Guardrail Validation]
    end
    
    subgraph "Scanner Service (Search Engine)"
        LiteralSearch[Ripgrep Scanner]
        SemanticSearch[Vector Search]
        HybridSearch[Hybrid Search]
        Ingestion[Data Ingestion]
    end
    
    subgraph "Vector & Data Layer"
        Qdrant[Qdrant VectorDB]
        Embedding[Embedding Service]
        CodeIndex[Code Index]
        DocIndex[Documentation Index]
    end
    
    subgraph "External Services"
        OpenAI[OpenAI API]
        Ollama[Local Ollama]
    end
    
    UI --> API
    Graph --> Panel
    Panel --> Banner
    
    API --> Orchestrator
    Orchestrator --> RealLLM
    RealLLM --> Guardrails
    Guardrails --> API
    
    Orchestrator --> LiteralSearch
    Orchestrator --> SemanticSearch
    LiteralSearch --> HybridSearch
    SemanticSearch --> HybridSearch
    
    HybridSearch --> Qdrant
    Ingestion --> Embedding
    Embedding --> CodeIndex
    Embedding --> DocIndex
    CodeIndex --> Qdrant
    DocIndex --> Qdrant
    
    RealLLM --> OpenAI
    RealLLM --> Ollama
    
    style UI fill:#e1f5fe
    style API fill:#f3e5f5
    style LiteralSearch fill:#e8f5e8
    style Qdrant fill:#fff3e0
    style OpenAI fill:#ffebee
```

## Data Flow for Investigation

```mermaid
sequenceDiagram
    participant User
    participant UI as React UI
    participant API as FastAPI
    participant Orchestrator
    participant LLM as LLM Service
    participant Scanner as Scanner Service
    participant VectorDB as Qdrant
    participant FileSystem as Code Files
    
    User->>UI: Submit investigation query
    UI->>API: POST /api/v1/investigate
    API->>Orchestrator: Start investigation
    Orchestrator->>LLM: Plan investigation
    
    LLM->>Scanner: literal_search(query)
    Scanner->>FileSystem: Ripgrep search
    FileSystem-->>Scanner: Match results
    Scanner-->>LLM: Literal matches
    
    LLM->>Scanner: dependency_analysis(paths)
    Scanner->>FileSystem: Analyze file relationships
    FileSystem-->>Scanner: Dependency graph
    Scanner-->>LLM: Dependencies
    
    LLM->>Scanner: semantic_search(concept)
    Scanner->>VectorDB: Vector similarity search
    VectorDB-->>Scanner: Semantic results
    Scanner-->>LLM: Semantic matches
    
    LLM->>LLM: Synthesize results
    LLM-->>Orchestrator: Impact analysis
    Orchestrator->>LLM: Apply guardrails
    LLM-->>Orchestrator: Validated results
    Orchestrator-->>API: Final impact report
    API-->>UI: Investigation results
    UI-->>User: Display dependency graph
```

## Component Integration Matrix

| Component | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Priority |
|-----------|-----------|-----------|-----------|-----------|----------|
| React UI | ✅ Basic | ✅ Enhanced | ✅ Interactive | ✅ Polished | High |
| FastAPI | ✅ Mock | ✅ Enhanced | ✅ Intelligent | ✅ Production | Critical |
| Mock LLM | ✅ Complete | ❌ Replaced | ❌ Replaced | ❌ Replaced | Medium |
| Real LLM | ❌ Not Started | ❌ Not Started | ✅ Integrated | ✅ Optimized | Critical |
| Scanner | ✅ Basic | ✅ Enhanced | ✅ Advanced | ✅ Optimized | High |
| VectorDB | ⚠️ Partial | ✅ Working | ✅ Enhanced | ✅ Optimized | High |
| Embedding | ❌ Missing | ✅ Implemented | ✅ Optimized | ✅ Production | Critical |
| Guardrails | ❌ Missing | ❌ Not Started | ✅ Implemented | ✅ Enhanced | Medium |

## Risk & Mitigation Timeline

```mermaid
graph LR
    subgraph "Phase 1 Risks"
        P1R1[Service Integration Issues]
        P1R2[Test Failures]
        P1R3[Mock Data Limitations]
    end
    
    subgraph "Phase 2 Risks"
        P2R1[Embedding Performance]
        P2R2[VectorDB Scaling]
        P2R3[Search Quality]
    end
    
    subgraph "Phase 3 Risks"
        P3R1[LLM Reliability]
        P3R2[Tool Calling Issues]
        P3R3[Response Quality]
    end
    
    subgraph "Phase 4 Risks"
        P4R1[Performance Bottlenecks]
        P4R2[Production Issues]
        P4R3[User Adoption]
    end
    
    P1R1 --> M1[Incremental Testing]
    P1R2 --> M2[Fallback Mechanisms]
    P1R3 --> M3[Real Data Integration]
    
    P2R1 --> M4[Caching Strategy]
    P2R2 --> M5[Performance Monitoring]
    P2R3 --> M6[Quality Metrics]
    
    P3R1 --> M7[Multiple LLM Support]
    P3R2 --> M8[Tool Validation]
    P3R3 --> M9[Guardrail System]
    
    P4R1 --> M10[Load Testing]
    P4R2 --> M11[Staging Environment]
    P4R3 --> M12[User Training]
```

## Success Metrics Dashboard

```mermaid
graph TB
    subgraph "Phase 1 Metrics"
        P1M1[Test Pass Rate > 95%]
        P1M2[Service Uptime > 99%]
        P1M3[Basic Investigation Flow]
    end
    
    subgraph "Phase 2 Metrics"
        P2M1[Semantic Search Relevance]
        P2M2[Embedding Performance < 5s]
        P2M3[VectorDB Query < 2s]
    end
    
    subgraph "Phase 3 Metrics"
        P3M1[LLM Analysis Quality]
        P3M2[Tool Call Success Rate]
        P3M3[Knowledge Gap Detection]
    end
    
    subgraph "Phase 4 Metrics"
        P4M1[Production Load Handling]
        P4M2[User Satisfaction Score]
        P4M3[System Response Time < 30s]
    end
    
    P1M1 --> P2M1
    P2M1 --> P3M1
    P3M1 --> P4M1
    
    style P1M1 fill:#e8f5e8
    style P2M1 fill:#e8f5e8
    style P3M1 fill:#e8f5e8
    style P4M1 fill:#e8f5e8
```

This visual representation provides multiple views of the implementation plan, including timeline, architecture, data flow, integration matrix, and risk mitigation strategies.