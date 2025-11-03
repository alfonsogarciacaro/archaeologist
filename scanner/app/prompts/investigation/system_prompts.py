"""
Investigation System Prompts

This module contains system prompts for different types of code investigation.
"""

class InvestigationPrompts:
    """System prompts for LLM investigation tasks"""
    
    SYSTEM_PROMPT = """You are an expert software architect investigating code changes in enterprise systems.

Your task is to analyze the impact of proposed changes by:
1. Finding exact matches using literal_search
2. Analyzing dependencies using dependency_analysis  
3. Discovering related code using semantic_search
4. Synthesizing findings into a comprehensive impact report

You must:
- Use the provided tools to gather evidence
- Be thorough in your analysis
- Identify potential knowledge gaps
- Provide clear reasoning for your conclusions
- Include confidence scores for your findings

Focus on understanding how changes propagate through the system and what might break."""
    
    USER_PROMPT_TEMPLATE = "Investigate this change: {query}"
    
    FOLLOW_UP_PROMPTS = {
        "missing_evidence": "Can you provide more specific details about what you're trying to change?",
        "broad_query": "Your query seems broad. Can you specify which component or file you're interested in?",
        "unclear_impact": "What specific impact are you concerned about (performance, security, functionality)?"
    }
    
    @classmethod
    def get_user_prompt(cls, query: str) -> str:
        """Generate user prompt from template"""
        return cls.USER_PROMPT_TEMPLATE.format(query=query)
    
    @classmethod
    def get_follow_up_prompt(cls, prompt_type: str) -> str:
        """Get follow-up prompt by type"""
        return cls.FOLLOW_UP_PROMPTS.get(prompt_type, "Can you provide more details?")