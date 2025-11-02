We need a high level map of what we want to do before we start coding.

What we have at the moment:
- The mock_enterprise: this represents an enterprise project (the tool should support multiple projects later), there are 2 main sources:
    - Live repos: git repos that we consider to be fresh (I'm still not sure if the tool will have access to git commands and synchronization itself)
    - Data lake: these are just files dropped by the user (manual upload for now, maybe automatic sync later) to represent parts of the system that are not directly accessible as code repos (e.g. legacy systems, databases, etc)
    - Metadata: not yet in mock_enterprise, but the tool should be able to attach metadata to sources or to the project as a whole (e.g. owner, description, tags, etc), with info from the user or from automatic analysis

- The services (not connected at the moment):
    - UI
    - API backend
    - Vector DB (Qdrant for now as Docker container)
    - Scanner: it will use
        - Text search: right now it is ripgrep but this doesn't work on Windows, is there a better option as Python library?
        - Semantic search: It should be able to RAG with the vector DB, but we haven't implemented embeddings yet, should we have a separate service for that as with the LLM or should we use a small embeddings model and call it directly from the scanner?
    - LLM service: it's not in this repo, we consider it to be an external service with an API (we can use local models with Ollama or remote services like OpenAI or Anthropic)
    
At the beginning we were thinking to call the LLM from the API so the API acted as an orchestrator, but I'm not sure because these calls take a while, maybe we should move it to the scanner?
In any case we need to decide how to coordinate the different searches (text, semantic, LLM agentic) and how to combine their results (have better confidence if multiple methods return similar results?).
Besides that, we need to create an initial map/graph of the sources and refine it with the results of the scans/investigations. Maybe at the beginning all the sources are disconnected nodes and we find links with the results of the investigations?