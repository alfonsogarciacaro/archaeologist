"""
Benchmarking Results Module

This module provides result storage, analysis, and reporting capabilities.
"""

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkMetrics:
    """Aggregated metrics for benchmark analysis"""
    mean_response_time: float
    median_response_time: float
    std_dev_response_time: float
    mean_accuracy: float
    mean_completeness: float
    mean_cost: float
    success_rate: float
    total_tests: int
    successful_tests: int

@dataclass
class ComparisonResult:
    """Result of comparing two configurations"""
    winner: str
    margin: float
    metric: str
    confidence: float
    details: Dict[str, Any]

class BenchmarkAnalyzer:
    """Analyzes benchmark results and provides insights"""
    
    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self.analysis_cache = {}
    
    def analyze_by_provider(self) -> Dict[str, BenchmarkMetrics]:
        """Analyze performance by LLM provider"""
        provider_results = self._group_by_field("provider")
        metrics = {}
        
        for provider, results in provider_results.items():
            metrics[provider] = self._calculate_metrics(results)
        
        return metrics
    
    def analyze_by_model(self) -> Dict[str, BenchmarkMetrics]:
        """Analyze performance by model"""
        model_results = self._group_by_field("model")
        metrics = {}
        
        for model, results in model_results.items():
            metrics[model] = self._calculate_metrics(results)
        
        return metrics
    
    def analyze_by_prompt_variant(self) -> Dict[str, BenchmarkMetrics]:
        """Analyze performance by prompt variant"""
        prompt_results = self._group_by_field("prompt_variant")
        metrics = {}
        
        for prompt, results in prompt_results.items():
            metrics[prompt] = self._calculate_metrics(results)
        
        return metrics
    
    def analyze_by_tool_combination(self) -> Dict[str, BenchmarkMetrics]:
        """Analyze performance by tool combination"""
        tool_results = self._group_by_field("tool_combination")
        metrics = {}
        
        for tools, results in tool_results.items():
            metrics[tools] = self._calculate_metrics(results)
        
        return metrics
    
    def find_best_configuration(self) -> Dict[str, Any]:
        """Find the best overall configuration"""
        successful_results = [r for r in self.results if not r.get("error")]
        
        if not successful_results:
            return {"error": "No successful results to analyze"}
        
        # Calculate combined score (accuracy + completeness) / 2
        best_result = None
        best_score = 0.0
        
        for result in successful_results:
            combined_score = (result.get("accuracy_score", 0) + result.get("completeness_score", 0)) / 2
            if combined_score > best_score:
                best_score = combined_score
                best_result = result
        
        if best_result:
            return {
                "best_configuration": {
                    "provider": best_result.get("provider"),
                    "model": best_result.get("model"),
                    "prompt_variant": best_result.get("prompt_variant"),
                    "tool_combination": best_result.get("tool_combination")
                },
                "performance": {
                    "combined_score": best_score,
                    "accuracy_score": best_result.get("accuracy_score"),
                    "completeness_score": best_result.get("completeness_score"),
                    "response_time_ms": best_result.get("response_time_ms"),
                    "cost_estimate": best_result.get("cost_estimate")
                },
                "query": best_result.get("query")
            }
        
        return {"error": "Could not determine best configuration"}
    
    def compare_configurations(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> ComparisonResult:
        """Compare two configurations and determine winner"""
        # Filter results for each configuration
        results1 = self._filter_results(config1)
        results2 = self._filter_results(config2)
        
        if not results1 or not results2:
            return ComparisonResult(
                winner="unknown",
                margin=0.0,
                metric="none",
                confidence=0.0,
                details={"error": "Insufficient data for comparison"}
            )
        
        # Calculate metrics for both
        metrics1 = self._calculate_metrics(results1)
        metrics2 = self._calculate_metrics(results2)
        
        # Compare on combined score
        score1 = (metrics1.mean_accuracy + metrics1.mean_completeness) / 2
        score2 = (metrics2.mean_accuracy + metrics2.mean_completeness) / 2
        
        if score1 > score2:
            winner = "config1"
            margin = score1 - score2
        else:
            winner = "config2"
            margin = score2 - score1
        
        # Calculate confidence based on sample size and variance
        confidence = self._calculate_confidence(results1, results2)
        
        return ComparisonResult(
            winner=winner,
            margin=margin,
            metric="combined_score",
            confidence=confidence,
            details={
                "config1_metrics": asdict(metrics1),
                "config2_metrics": asdict(metrics2),
                "config1_score": score1,
                "config2_score": score2
            }
        )
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        return {
            "summary": self._generate_summary(),
            "provider_analysis": self._analyze_provider_performance(),
            "prompt_analysis": self._analyze_prompt_effectiveness(),
            "tool_analysis": self._analyze_tool_performance(),
            "best_configuration": self.find_best_configuration(),
            "recommendations": self._generate_recommendations(),
            "detailed_results": self.results
        }
    
    def _group_by_field(self, field: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group results by specified field"""
        groups = {}
        for result in self.results:
            key = result.get(field, "unknown")
            if key not in groups:
                groups[key] = []
            groups[key].append(result)
        return groups
    
    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> BenchmarkMetrics:
        """Calculate metrics for a group of results"""
        successful_results = [r for r in results if not r.get("error")]
        
        if not successful_results:
            return BenchmarkMetrics(
                mean_response_time=0.0,
                median_response_time=0.0,
                std_dev_response_time=0.0,
                mean_accuracy=0.0,
                mean_completeness=0.0,
                mean_cost=0.0,
                success_rate=0.0,
                total_tests=len(results),
                successful_tests=0
            )
        
        response_times = [r.get("response_time_ms", 0) for r in successful_results]
        accuracies = [r.get("accuracy_score", 0) for r in successful_results]
        completenesses = [r.get("completeness_score", 0) for r in successful_results]
        costs = [r.get("cost_estimate", 0) for r in successful_results]
        
        return BenchmarkMetrics(
            mean_response_time=statistics.mean(response_times),
            median_response_time=statistics.median(response_times),
            std_dev_response_time=statistics.stdev(response_times) if len(response_times) > 1 else 0.0,
            mean_accuracy=statistics.mean(accuracies),
            mean_completeness=statistics.mean(completenesses),
            mean_cost=statistics.mean(costs),
            success_rate=len(successful_results) / len(results),
            total_tests=len(results),
            successful_tests=len(successful_results)
        )
    
    def _filter_results(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter results matching configuration"""
        filtered = []
        for result in self.results:
            match = True
            for key, value in config.items():
                if result.get(key) != value:
                    match = False
                    break
            if match:
                filtered.append(result)
        return filtered
    
    def _calculate_confidence(self, results1: List[Dict[str, Any]], results2: List[Dict[str, Any]]) -> float:
        """Calculate confidence in comparison result"""
        # Simple confidence based on sample size
        min_sample_size = min(len(results1), len(results2))
        
        if min_sample_size < 3:
            return 0.3  # Low confidence
        elif min_sample_size < 10:
            return 0.6  # Medium confidence
        else:
            return 0.9  # High confidence
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if not r.get("error")])
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "providers_tested": list(set(r.get("provider") for r in self.results)),
            "models_tested": list(set(r.get("model") for r in self.results)),
            "prompt_variants_tested": list(set(r.get("prompt_variant") for r in self.results)),
            "tool_combinations_tested": list(set(r.get("tool_combination") for r in self.results))
        }
    
    def _analyze_provider_performance(self) -> Dict[str, Any]:
        """Analyze and rank providers"""
        provider_metrics = self.analyze_by_provider()
        
        # Rank by combined score
        ranked_providers = []
        for provider, metrics in provider_metrics.items():
            combined_score = (metrics.mean_accuracy + metrics.mean_completeness) / 2
            ranked_providers.append({
                "provider": provider,
                "combined_score": combined_score,
                "metrics": asdict(metrics)
            })
        
        ranked_providers.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return {
            "ranked_providers": ranked_providers,
            "best_provider": ranked_providers[0]["provider"] if ranked_providers else None,
            "performance_spread": {
                "best_score": ranked_providers[0]["combined_score"] if ranked_providers else 0,
                "worst_score": ranked_providers[-1]["combined_score"] if ranked_providers else 0
            }
        }
    
    def _analyze_prompt_effectiveness(self) -> Dict[str, Any]:
        """Analyze prompt variant effectiveness"""
        prompt_metrics = self.analyze_by_prompt_variant()
        
        # Rank by effectiveness
        ranked_prompts = []
        for prompt, metrics in prompt_metrics.items():
            effectiveness = (metrics.mean_accuracy + metrics.mean_completeness) / 2
            ranked_prompts.append({
                "prompt_variant": prompt,
                "effectiveness_score": effectiveness,
                "metrics": asdict(metrics)
            })
        
        ranked_prompts.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        
        return {
            "ranked_prompts": ranked_prompts,
            "most_effective": ranked_prompts[0]["prompt_variant"] if ranked_prompts else None,
            "effectiveness_insights": self._generate_prompt_insights(ranked_prompts)
        }
    
    def _analyze_tool_performance(self) -> Dict[str, Any]:
        """Analyze tool combination performance"""
        tool_metrics = self.analyze_by_tool_combination()
        
        # Rank by performance
        ranked_tools = []
        for tools, metrics in tool_metrics.items():
            performance = (metrics.mean_accuracy + metrics.mean_completeness) / 2
            ranked_tools.append({
                "tool_combination": tools,
                "performance_score": performance,
                "metrics": asdict(metrics)
            })
        
        ranked_tools.sort(key=lambda x: x["performance_score"], reverse=True)
        
        return {
            "ranked_combinations": ranked_tools,
            "best_combination": ranked_tools[0]["tool_combination"] if ranked_tools else None,
            "performance_insights": self._generate_tool_insights(ranked_tools)
        }
    
    def _generate_prompt_insights(self, ranked_prompts: List[Dict[str, Any]]) -> List[str]:
        """Generate insights about prompt effectiveness"""
        insights = []
        
        if len(ranked_prompts) >= 2:
            best = ranked_prompts[0]
            worst = ranked_prompts[-1]
            improvement = best["effectiveness_score"] - worst["effectiveness_score"]
            
            if improvement > 0.2:
                insights.append(f"Best prompt ({best['prompt_variant']}) significantly outperforms worst by {improvement:.2f}")
            
            # Check for patterns
            detailed_prompts = [p for p in ranked_prompts if "detailed" in p["prompt_variant"]]
            concise_prompts = [p for p in ranked_prompts if "concise" in p["prompt_variant"]]
            
            if detailed_prompts and concise_prompts:
                avg_detailed = sum(p["effectiveness_score"] for p in detailed_prompts) / len(detailed_prompts)
                avg_concise = sum(p["effectiveness_score"] for p in concise_prompts) / len(concise_prompts)
                
                if avg_detailed > avg_concise:
                    insights.append("Detailed prompts tend to be more effective than concise ones")
                else:
                    insights.append("Concise prompts perform as well as detailed ones")
        
        return insights
    
    def _generate_tool_insights(self, ranked_tools: List[Dict[str, Any]]) -> List[str]:
        """Generate insights about tool combination performance"""
        insights = []
        
        if len(ranked_tools) >= 2:
            best = ranked_tools[0]
            worst = ranked_tools[-1]
            improvement = best["performance_score"] - worst["performance_score"]
            
            if improvement > 0.15:
                insights.append(f"Best tool combination ({best['tool_combination']}) significantly outperforms worst by {improvement:.2f}")
            
            # Check patterns
            all_tools = [t for t in ranked_tools if "all" in t["tool_combination"]]
            minimal_tools = [t for t in ranked_tools if "minimal" in t["tool_combination"]]
            
            if all_tools and minimal_tools:
                avg_all = sum(t["performance_score"] for t in all_tools) / len(all_tools)
                avg_minimal = sum(t["performance_score"] for t in minimal_tools) / len(minimal_tools)
                
                if avg_all > avg_minimal:
                    insights.append("Comprehensive tool combinations provide better results than minimal ones")
                else:
                    insights.append("Minimal tool combinations can be as effective as comprehensive ones")
        
        return insights
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Analyze provider performance
        provider_analysis = self._analyze_provider_performance()
        if provider_analysis.get("best_provider"):
            recommendations.append(f"Use {provider_analysis['best_provider']} as primary LLM provider")
        
        # Analyze prompt effectiveness
        prompt_analysis = self._analyze_prompt_effectiveness()
        if prompt_analysis.get("most_effective"):
            recommendations.append(f"Use {prompt_analysis['most_effective']} prompt variant for best results")
        
        # Analyze tool performance
        tool_analysis = self._analyze_tool_performance()
        if tool_analysis.get("best_combination"):
            recommendations.append(f"Use {tool_analysis['best_combination']} tool combination")
        
        # Cost considerations
        provider_metrics = self.analyze_by_provider()
        cost_effective = []
        for provider, metrics in provider_metrics.items():
            if metrics.mean_cost == 0:
                cost_effective.append(provider)
        
        if cost_effective:
            recommendations.append(f"Consider cost-effective providers: {', '.join(cost_effective)}")
        
        return recommendations

class BenchmarkReporter:
    """Generates formatted benchmark reports"""
    
    def __init__(self, analyzer: BenchmarkAnalyzer):
        self.analyzer = analyzer
    
    def save_report(self, output_path: str, format: str = "json") -> str:
        """Save report to file"""
        report = self.analyzer.generate_report()
        
        if format.lower() == "json":
            return self._save_json_report(report, output_path)
        elif format.lower() == "markdown":
            return self._save_markdown_report(report, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _save_json_report(self, report: Dict[str, Any], output_path: str) -> str:
        """Save report as JSON"""
        filepath = Path(output_path)
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        return str(filepath)
    
    def _save_markdown_report(self, report: Dict[str, Any], output_path: str) -> str:
        """Save report as Markdown"""
        filepath = Path(output_path)
        
        markdown_content = self._generate_markdown_content(report)
        
        with open(filepath, 'w') as f:
            f.write(markdown_content)
        
        return str(filepath)
    
    def _generate_markdown_content(self, report: Dict[str, Any]) -> str:
        """Generate markdown content from report"""
        content = []
        
        # Title and summary
        content.append("# LLM Benchmark Report")
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("")
        
        # Summary
        summary = report.get("summary", {})
        content.append("## Summary")
        content.append(f"- Total Tests: {summary.get('total_tests', 0)}")
        content.append(f"- Success Rate: {summary.get('success_rate', 0):.2%}")
        content.append(f"- Providers Tested: {', '.join(summary.get('providers_tested', []))}")
        content.append("")
        
        # Best Configuration
        best_config = report.get("best_configuration", {})
        if "best_configuration" in best_config:
            config = best_config["best_configuration"]
            content.append("## Best Configuration")
            content.append(f"- Provider: {config.get('provider')}")
            content.append(f"- Model: {config.get('model')}")
            content.append(f"- Prompt Variant: {config.get('prompt_variant')}")
            content.append(f"- Tool Combination: {config.get('tool_combination')}")
            content.append("")
        
        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            content.append("## Recommendations")
            for rec in recommendations:
                content.append(f"- {rec}")
            content.append("")
        
        return "\n".join(content)