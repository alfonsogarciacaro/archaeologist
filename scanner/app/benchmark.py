"""
RAG Testing and Benchmarking Framework

This module provides comprehensive testing and benchmarking tools for the RAG system,
including search quality evaluation, performance measurement, and model comparison.
"""

import time
import json
import asyncio
import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from app.rag.rag_service import get_rag_service
from app.rag.models import IngestRequest, SearchRequest
from app.config import get_settings


@dataclass
class BenchmarkResult:
    """Results from a benchmark test"""
    test_name: str
    model_name: str
    search_quality_score: float
    avg_response_time_ms: float
    memory_usage_mb: float
    total_documents: int
    total_chunks: int
    embeddings_per_second: float
    search_queries_per_second: float
    error_rate: float


@dataclass
class QualityTestCase:
    """Test case for search quality evaluation"""
    query: str
    expected_files: List[str]
    expected_functions: List[str]
    expected_keywords: List[str]
    description: str


class RAGBenchmark:
    """
    Comprehensive benchmarking tool for RAG system.
    
    This class provides:
    - Search quality evaluation with relevance scoring
    - Performance measurement (time, memory, throughput)
    - Model comparison capabilities
    - Automated test suite execution
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.rag_service = None
        self.test_data = self._load_test_data()
    
    async def initialize(self) -> None:
        """Initialize benchmark framework"""
        if self.rag_service is None:
            self.rag_service = await get_rag_service()
    
    def _load_test_data(self) -> Dict[str, Any]:
        """Load test data for quality evaluation"""
        return {
            "test_documents": [
                {
                    "file_name": "user_auth_service.py",
                    "project": "test_project",
                    "content": '''
import hashlib
import bcrypt
from typing import Optional, Dict

class UserService:
    """Service for user authentication and management"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password"""
        query = "SELECT id, username, email, password_hash FROM users WHERE username = ?"
        user_data = self.db.execute(query, (username,)).fetchone()
        
        if not user_data:
            return None
        
        if self.verify_password(password, user_data['password_hash']):
            return {
                'user_id': user_data['id'],
                'username': user_data['username'],
                'email': user_data['email']
            }
        
        return None
    
    def create_user(self, username: str, password: str, email: str) -> Dict:
        """Create new user account"""
        # Check if user already exists
        existing = self.db.execute(
            "SELECT id FROM users WHERE username = ?", 
            (username,)
        ).fetchone()
        
        if existing:
            raise ValueError("Username already exists")
        
        # Create new user
        password_hash = self.hash_password(password)
        user_id = self.db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        ).lastrowid
        
        return {
            'user_id': user_id,
            'username': username,
            'email': email
        }
''',
                    "file_type": "python",
                    "timestamp": "2023-10-27T10:30:00Z"
                },
                {
                    "file_name": "database_schema.sql",
                    "project": "test_project", 
                    "content": '''
-- User management database schema
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User preferences table
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    preference_key VARCHAR(50) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
''',
                    "file_type": "sql",
                    "timestamp": "2023-10-27T10:30:00Z"
                },
                {
                    "file_name": "payment_processor.js",
                    "project": "test_project",
                    "content": r'''
class PaymentProcessor {
    constructor(apiKey, merchantId) {
        this.apiKey = apiKey;
        this.merchantId = merchantId;
        this.baseUrl = 'https://api.payment-provider.com/v1';
    }
    
    async processPayment(paymentData) {
        const {
            amount,
            currency,
            cardNumber,
            expiryMonth,
            expiryYear,
            cvv,
            customerEmail
        } = paymentData;
        
        // Validate payment data
        if (!this._validatePaymentData(paymentData)) {
            throw new Error('Invalid payment data');
        }
        
        // Create payment request
        const paymentRequest = {
            merchant_id: this.merchantId,
            amount: amount,
            currency: currency,
            payment_method: {
                type: 'credit_card',
                card_number: this._maskCardNumber(cardNumber),
                expiry_month: expiryMonth,
                expiry_year: expiryYear,
                cvv: cvv
            },
            customer: {
                email: customerEmail
            },
            metadata: {
                timestamp: new Date().toISOString(),
                source: 'web_app'
            }
        };
        
        try {
            const response = await fetch(`${this.baseUrl}/payments`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(paymentRequest)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                return {
                    success: true,
                    transactionId: result.transaction_id,
                    amount: result.amount,
                    currency: result.currency,
                    status: result.status
                };
            } else {
                throw new Error(result.error_message);
            }
            
        } catch (error) {
            console.error('Payment processing failed:', error);
            throw error;
        }
    }
    
    _validatePaymentData(paymentData) {
        const { amount, currency, cardNumber, expiryMonth, expiryYear, cvv } = paymentData;
        
        // Basic validation
        if (!amount || amount <= 0) {
            return false;
        }
        
        if (!currency || currency.length !== 3) {
            return false;
        }
        
        if (!cardNumber || !this._isValidCardNumber(cardNumber)) {
            return false;
        }
        
        if (!expiryMonth || !expiryYear || !this._isCardExpired(expiryMonth, expiryYear)) {
            return false;
        }
        
        if (!cvv || cvv.length < 3 || cvv.length > 4) {
            return false;
        }
        
        return true;
    }
    
    _isValidCardNumber(cardNumber) {
        // Remove spaces and dashes
        const cleaned = cardNumber.replace(/[\s-]/g, '');
        
        // Check if it's all digits and valid length
        if (!/^\d+$/.test(cleaned) || cleaned.length < 13 || cleaned.length > 19) {
            return false;
        }
        
        // Luhn algorithm check
        let sum = 0;
        let isEven = false;
        
        for (let i = cleaned.length - 1; i >= 0; i--) {
            let digit = parseInt(cleaned[i]);
            
            if (isEven) {
                digit *= 2;
                if (digit > 9) {
                    digit -= 9;
                }
            }
            
            sum += digit;
            isEven = !isEven;
        }
        
        return sum % 10 === 0;
    }
    
    _isCardExpired(expiryMonth, expiryYear) {
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        
        if (expiryYear < currentYear) {
            return true; // Expired
        }
        
        if (expiryYear === currentYear && expiryMonth < currentMonth) {
            return true; // Expired
        }
        
        return false; // Not expired
    }
    
    _maskCardNumber(cardNumber) {
        const cleaned = cardNumber.replace(/[\s-]/g, '');
        if (cleaned.length <= 4) {
            return cleaned;
        }
        
        const lastFour = cleaned.slice(-4);
        const maskedLength = cleaned.length - 4;
        return '*'.repeat(maskedLength) + lastFour;
    }
}

module.exports = PaymentProcessor;
''',
                    "file_type": "javascript",
                    "timestamp": "2023-10-27T10:30:00Z"
                }
            ],
            "quality_test_cases": [
                QualityTestCase(
                    query="user authentication password hashing",
                    expected_files=["user_auth_service.py"],
                    expected_functions=["hash_password", "verify_password", "authenticate_user"],
                    expected_keywords=["bcrypt", "password", "authentication"],
                    description="Test user authentication functionality search"
                ),
                QualityTestCase(
                    query="database schema user table creation",
                    expected_files=["database_schema.sql"],
                    expected_functions=["CREATE TABLE users"],
                    expected_keywords=["users", "schema", "table"],
                    description="Test database schema search"
                ),
                QualityTestCase(
                    query="payment processing credit card validation",
                    expected_files=["payment_processor.js"],
                    expected_functions=["processPayment", "_validatePaymentData"],
                    expected_keywords=["payment", "credit card", "validation"],
                    description="Test payment processing search"
                ),
                QualityTestCase(
                    query="user creation and validation",
                    expected_files=["user_auth_service.py"],
                    expected_functions=["create_user"],
                    expected_keywords=["create", "user", "validation"],
                    description="Test user creation functionality"
                ),
                QualityTestCase(
                    query="Luhn algorithm card number validation",
                    expected_files=["payment_processor.js"],
                    expected_functions=["_isValidCardNumber"],
                    expected_keywords=["Luhn", "card number", "validation"],
                    description="Test specific algorithm search"
                )
            ]
        }
    
    async def ingest_test_documents(self) -> Dict[str, Any]:
        """Ingest test documents for benchmarking"""
        print("📥 Ingesting test documents...")
        
        ingest_results = []
        total_chunks = 0
        total_time = 0
        
        for doc in self.test_data["test_documents"]:
            start_time = time.time()
            
            request = IngestRequest(
                file_name=doc["file_name"],
                project=doc["project"],
                content=doc["content"],
                file_type=doc["file_type"],
                timestamp=doc["timestamp"]
            )
            
            result = await self.rag_service.ingest_document(request)
            
            ingest_time = time.time() - start_time
            total_time += ingest_time
            total_chunks += result.chunks_created
            
            ingest_results.append({
                "file": doc["file_name"],
                "chunks": result.chunks_created,
                "time_ms": int(ingest_time * 1000),
                "collection": result.collection_name
            })
            
            print(f"  ✅ {doc['file_name']}: {result.chunks_created} chunks in {ingest_time:.3f}s")
        
        return {
            "ingest_results": ingest_results,
            "total_documents": len(self.test_data["test_documents"]),
            "total_chunks": total_chunks,
            "total_time_ms": int(total_time * 1000),
            "avg_time_per_doc_ms": int((total_time / len(self.test_data["test_documents"])) * 1000)
        }
    
    async def run_search_quality_tests(self) -> Dict[str, Any]:
        """Run search quality evaluation tests"""
        print("🔍 Running search quality tests...")
        
        quality_results = []
        
        for test_case in self.test_data["quality_test_cases"]:
            print(f"  🧪 Testing: {test_case.description}")
            
            start_time = time.time()
            
            search_request = SearchRequest(
                query=test_case.query,
                project="test_project",
                limit=10,
                score_threshold=0.3
            )
            
            search_result = await self.rag_service.search(search_request)
            
            search_time = time.time() - start_time
            
            # Evaluate quality
            quality_score = self._evaluate_search_quality(search_result.results, test_case)
            
            quality_results.append({
                "query": test_case.query,
                "description": test_case.description,
                "expected_files": test_case.expected_files,
                "expected_functions": test_case.expected_functions,
                "expected_keywords": test_case.expected_keywords,
                "results_count": len(search_result.results),
                "search_time_ms": int(search_time * 1000),
                "quality_score": quality_score,
                "top_result": search_result.results[0] if search_result.results else None,
                "all_results": search_result.results
            })
            
            print(f"    Score: {quality_score:.2f}, Results: {len(search_result.results)}, Time: {search_time:.3f}s")
        
        # Calculate overall quality metrics
        avg_quality = statistics.mean([r["quality_score"] for r in quality_results])
        avg_search_time = statistics.mean([r["search_time_ms"] for r in quality_results])
        
        return {
            "quality_results": quality_results,
            "avg_quality_score": avg_quality,
            "avg_search_time_ms": avg_search_time,
            "total_tests": len(quality_results)
        }
    
    def _evaluate_search_quality(self, results: List, test_case: QualityTestCase) -> float:
        """Evaluate search quality against expected results"""
        if not results:
            return 0.0
        
        # Score components
        file_relevance_score = 0.0
        function_relevance_score = 0.0
        keyword_relevance_score = 0.0
        
        # Check file relevance
        found_files = [r.metadata.get("file_name", "") for r in results]
        for expected_file in test_case.expected_files:
            if any(expected_file in found_file for found_file in found_files):
                file_relevance_score += 1.0
        file_relevance_score = file_relevance_score / len(test_case.expected_files)
        
        # Check function relevance
        all_content = " ".join([r.content.lower() for r in results])
        for expected_function in test_case.expected_functions:
            if expected_function.lower() in all_content:
                function_relevance_score += 1.0
        function_relevance_score = function_relevance_score / len(test_case.expected_functions)
        
        # Check keyword relevance
        for expected_keyword in test_case.expected_keywords:
            if expected_keyword.lower() in all_content:
                keyword_relevance_score += 1.0
        keyword_relevance_score = keyword_relevance_score / len(test_case.expected_keywords)
        
        # Weighted average (files are most important)
        total_score = (
            file_relevance_score * 0.5 +
            function_relevance_score * 0.3 +
            keyword_relevance_score * 0.2
        )
        
        return min(total_score, 1.0)
    
    async def run_performance_benchmark(self, num_iterations: int = 100) -> Dict[str, Any]:
        """Run performance benchmark tests"""
        print(f"⚡ Running performance benchmark ({num_iterations} iterations)...")
        
        # Test embedding performance
        embedding_times = []
        test_texts = [
            "This is a test document for embedding generation.",
            "User authentication with password hashing and verification.",
            "Database schema with user management tables.",
            "Payment processing with credit card validation."
        ]
        
        for i in range(num_iterations):
            start_time = time.time()
            await self.rag_service.embedding_model.embed_batch(test_texts)
            embedding_time = time.time() - start_time
            embedding_times.append(embedding_time)
            
            if (i + 1) % 20 == 0:
                print(f"    Embedding progress: {i + 1}/{num_iterations}")
        
        # Test search performance
        search_times = []
        test_queries = [
            "user authentication",
            "database schema", 
            "payment processing",
            "password hashing"
        ]
        
        for i in range(num_iterations):
            query = test_queries[i % len(test_queries)]
            start_time = time.time()
            
            search_request = SearchRequest(
                query=query,
                project="test_project",
                limit=5
            )
            
            await self.rag_service.search(search_request)
            search_time = time.time() - start_time
            search_times.append(search_time)
            
            if (i + 1) % 20 == 0:
                print(f"    Search progress: {i + 1}/{num_iterations}")
        
        # Calculate statistics
        avg_embedding_time = statistics.mean(embedding_times)
        avg_search_time = statistics.mean(search_times)
        
        return {
            "embedding_performance": {
                "avg_time_per_batch_ms": int(avg_embedding_time * 1000),
                "min_time_ms": int(min(embedding_times) * 1000),
                "max_time_ms": int(max(embedding_times) * 1000),
                "embeddings_per_second": len(test_texts) / avg_embedding_time,
                "total_iterations": num_iterations
            },
            "search_performance": {
                "avg_time_ms": int(avg_search_time * 1000),
                "min_time_ms": int(min(search_times) * 1000),
                "max_time_ms": int(max(search_times) * 1000),
                "searches_per_second": 1.0 / avg_search_time,
                "total_iterations": num_iterations
            }
        }
    
    async def run_memory_usage_test(self) -> Dict[str, Any]:
        """Test memory usage during operations"""
        print("💾 Running memory usage test...")
        
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            print("    ⚠️  psutil not available, skipping memory test")
            return {"error": "psutil not available"}
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Ingest documents and measure memory
        await self.ingest_test_documents()
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run search operations
        for _ in range(50):
            search_request = SearchRequest(
                query="user authentication",
                project="test_project",
                limit=5
            )
            await self.rag_service.search(search_request)
        
        search_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "baseline_memory_mb": baseline_memory,
            "peak_memory_mb": peak_memory,
            "search_memory_mb": search_memory,
            "memory_increase_mb": peak_memory - baseline_memory,
            "memory_per_chunk_kb": ((peak_memory - baseline_memory) * 1024) / 100  # Assuming ~100 chunks
        }
    
    async def run_full_benchmark(self) -> BenchmarkResult:
        """Run complete benchmark suite"""
        print("🚀 Starting full RAG benchmark...")
        start_time = time.time()
        
        # Initialize
        await self.initialize()
        
        # Run all tests
        ingest_results = await self.ingest_test_documents()
        quality_results = await self.run_search_quality_tests()
        performance_results = await self.run_performance_benchmark()
        memory_results = await self.run_memory_usage_test()
        
        total_time = time.time() - start_time
        
        # Create benchmark result
        result = BenchmarkResult(
            test_name="Full RAG Benchmark",
            model_name=self.rag_service.embedding_model.get_model_info()["model_name"],
            search_quality_score=quality_results["avg_quality_score"],
            avg_response_time_ms=quality_results["avg_search_time_ms"],
            memory_usage_mb=memory_results.get("peak_memory_mb", 0),
            total_documents=ingest_results["total_documents"],
            total_chunks=ingest_results["total_chunks"],
            embeddings_per_second=performance_results["embedding_performance"]["embeddings_per_second"],
            search_queries_per_second=performance_results["search_performance"]["searches_per_second"],
            error_rate=0.0  # TODO: Track errors during tests
        )
        
        # Print summary
        self._print_benchmark_summary(result, {
            "ingest": ingest_results,
            "quality": quality_results,
            "performance": performance_results,
            "memory": memory_results
        })
        
        return result
    
    def _print_benchmark_summary(self, result: BenchmarkResult, detailed_results: Dict) -> None:
        """Print comprehensive benchmark summary"""
        print("\n" + "="*80)
        print("📊 RAG BENCHMARK SUMMARY")
        print("="*80)
        
        print(f"\n🤖 Model: {result.model_name}")
        print(f"📁 Documents: {result.total_documents}")
        print(f"🧩 Chunks: {result.total_chunks}")
        
        print(f"\n🎯 Search Quality: {result.search_quality_score:.2f}/1.00")
        print(f"⚡ Avg Response Time: {result.avg_response_time_ms:.0f}ms")
        print(f"🔍 Search Throughput: {result.search_queries_per_second:.1f} queries/sec")
        print(f"📈 Embedding Throughput: {result.embeddings_per_second:.1f} embeddings/sec")
        print(f"💾 Memory Usage: {result.memory_usage_mb:.1f}MB")
        
        # Quality details
        quality = detailed_results["quality"]
        print(f"\n📋 Quality Test Results:")
        for test_result in quality["quality_results"][:3]:  # Show top 3
            status = "✅" if test_result["quality_score"] > 0.7 else "⚠️" if test_result["quality_score"] > 0.4 else "❌"
            print(f"  {status} {test_result['description']}: {test_result['quality_score']:.2f}")
        
        # Performance details
        perf = detailed_results["performance"]
        print(f"\n⚡ Performance Details:")
        print(f"  Embedding: {perf['embedding_performance']['avg_time_per_batch_ms']}ms avg, {perf['embedding_performance']['embeddings_per_second']:.1f}/sec")
        print(f"  Search: {perf['search_performance']['avg_time_ms']}ms avg, {perf['search_performance']['searches_per_second']:.1f}/sec")
        
        print("\n" + "="*80)


# CLI interface for running benchmarks
async def main():
    """Main function for running benchmarks"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Benchmark Tool")
    parser.add_argument("--type", choices=["full", "quality", "performance", "memory"], 
                       default="full", help="Type of benchmark to run")
    parser.add_argument("--iterations", type=int, default=100, 
                       help="Number of iterations for performance tests")
    parser.add_argument("--output", type=str, help="Output file for results")
    
    args = parser.parse_args()
    
    benchmark = RAGBenchmark()
    
    if args.type == "full":
        result = await benchmark.run_full_benchmark()
    elif args.type == "quality":
        await benchmark.initialize()
        result = await benchmark.run_search_quality_tests()
    elif args.type == "performance":
        await benchmark.initialize()
        result = await benchmark.run_performance_benchmark(args.iterations)
    elif args.type == "memory":
        await benchmark.initialize()
        result = await benchmark.run_memory_usage_test()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n📄 Results saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())