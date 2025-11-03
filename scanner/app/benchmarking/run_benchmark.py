#!/usr/bin/env python3
"""
LLM Benchmark Runner

This script runs comprehensive benchmarks of LLM providers, prompts, and tools.
Usage: python -m scanner.app.benchmarking.run_benchmark
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from scanner.app.benchmarking.models import get_all_model_configs
from scanner.app.benchmarking.prompts import get_all_prompt_variants
from scanner.app.benchmarking.tools import get_all_tool_combinations

# Test queries for benchmarking
TEST_QUERIES = [
    "Update user authentication service",
    "Add new payment processing feature", 
    "Refactor database connection logic",
    "Implement caching layer"
]

async def run_quick_benchmark():
    """Run a quick benchmark using mock provider"""
    # Configure logging
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    
    print("🚀 Starting Quick LLM Benchmark")
    print("=" * 50)
    
    # Get configurations
    models = get_all_model_configs()
    prompts = get_all_prompt_variants()
    tools = get_all_tool_combinations()
    
    print(f"📊 Available Models: {list(models.keys())}")
    print(f"📝 Available Prompts: {list(prompts.keys())}")
    print(f"🔧 Available Tools: {list(tools.keys())}")
    print()
    
    # Test mock configuration
    print("🧪 Testing Mock Configuration...")
    
    try:
        # Import here to avoid circular imports
        from scanner.app.llm.llm_interface import LLMFactory
        
        # Create mock provider
        provider = await LLMFactory.create_provider()
        
        # Test health check
        print("🔍 Testing health check...")
        try:
            health = await provider.health_check()
            print(f"✅ Health Check: {health}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Test investigation
        test_query = "Update user authentication service"
        print(f"🔍 Testing investigation: {test_query}")
        
        try:
            result = await provider.investigate_change(test_query)
            
            if "error" in result:
                print(f"❌ Investigation failed: {result['error']}")
                print(f"📄 Full error response: {result}")
            else:
                print("✅ Investigation successful!")
                print(f"   - Nodes found: {len(result.get('nodes', []))}")
                print(f"   - Edges found: {len(result.get('edges', []))}")
                print(f"   - Knowledge gaps: {len(result.get('knowledge_gaps', []))}")
                
                explanation = result.get('explanation', {})
                if explanation:
                    print(f"   - Confidence: {explanation.get('confidence_score', 0):.2f}")
                    print(f"   - Reasoning steps: {len(explanation.get('reasoning_steps', []))}")
                
                # Show sample of response for debugging
                print(f"📄 Response keys: {list(result.keys())}")
                if 'nodes' in result and result['nodes']:
                    print(f"📄 Sample node: {result['nodes'][0]}")
                if 'edges' in result and result['edges']:
                    print(f"📄 Sample edge: {result['edges'][0]}")
                    
        except Exception as e:
            print(f"❌ Investigation failed with exception: {e}")
            print(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
        print()
        print("🎯 Quick benchmark completed successfully!")
        print("📈 Ready for comprehensive benchmarking")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

async def run_comprehensive_benchmark():
    """Run comprehensive benchmark across all configurations"""
    print("🚀 Starting Comprehensive LLM Benchmark")
    print("=" * 60)
    
    # This would implement the full benchmarking logic
    # For now, just show what would be tested
    
    models = get_all_model_configs()
    prompts = get_all_prompt_variants()
    tools = get_all_tool_combinations()
    
    total_combinations = len(models) * len(prompts) * len(tools) * len(TEST_QUERIES)
    
    print(f"📊 Benchmark Scope:")
    print(f"   - Models: {len(models)}")
    print(f"   - Prompts: {len(prompts)}")
    print(f"   - Tool Combinations: {len(tools)}")
    print(f"   - Test Queries: {len(TEST_QUERIES)}")
    print(f"   - Total Tests: {total_combinations}")
    print()
    
    print("⚠️  Comprehensive benchmark not yet implemented")
    print("📝 Use quick benchmark for testing")

def main():
    """Main benchmark runner"""
    if len(sys.argv) > 1 and sys.argv[1] == "--comprehensive":
        asyncio.run(run_comprehensive_benchmark())
    else:
        asyncio.run(run_quick_benchmark())

if __name__ == "__main__":
    main()