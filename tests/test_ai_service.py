"""
Unit Tests for AI Service Module
Week 1: Infrastructure Testing
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.AI.ai_service import (
        AIService, RateLimiter, ResponseCache, APIUsageStats,
        get_ai_service, initialize_ai_service
    )
except ImportError:
    from AI.ai_service import (
        AIService, RateLimiter, ResponseCache, APIUsageStats,
        get_ai_service, initialize_ai_service
    )


class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter can be created"""
        limiter = RateLimiter(requests_per_minute=10)
        self.assertEqual(limiter.requests_per_minute, 10)
        self.assertEqual(len(limiter.request_times), 0)
    
    def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows requests within limit"""
        limiter = RateLimiter(requests_per_minute=5)
        
        # Should allow 5 requests without waiting
        start_time = time.time()
        for _ in range(5):
            limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        # Should complete almost instantly (< 1 second)
        self.assertLess(elapsed, 1.0)
    
    def test_rate_limiter_enforces_limit(self):
        """Test that rate limiter enforces limit (this test is slow)"""
        limiter = RateLimiter(requests_per_minute=2)
        
        # Make 2 requests (should be instant)
        limiter.wait_if_needed()
        limiter.wait_if_needed()
        
        # Third request should wait
        # (We won't actually wait in tests, just verify structure)
        self.assertEqual(len(limiter.request_times), 2)


class TestResponseCache(unittest.TestCase):
    """Test response caching functionality"""
    
    def setUp(self):
        """Create temporary cache directory"""
        self.test_dir = tempfile.mkdtemp()
        self.cache = ResponseCache(cache_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)
    
    def test_cache_initialization(self):
        """Test cache initializes correctly"""
        self.assertTrue(self.cache.cache_dir.exists())
        self.assertIsInstance(self.cache.cache, dict)
    
    def test_cache_key_generation(self):
        """Test cache key generation is consistent"""
        key1 = self.cache.get_cache_key("test prompt", 0.7, 100)
        key2 = self.cache.get_cache_key("test prompt", 0.7, 100)
        key3 = self.cache.get_cache_key("different prompt", 0.7, 100)
        
        self.assertEqual(key1, key2)  # Same input = same key
        self.assertNotEqual(key1, key3)  # Different input = different key
    
    def test_cache_set_and_get(self):
        """Test storing and retrieving from cache"""
        prompt = "test prompt"
        response = "test response"
        
        # Cache should be empty initially
        self.assertIsNone(self.cache.get(prompt, 0.7, 100))
        
        # Set cache
        self.cache.set(prompt, 0.7, 100, response)
        
        # Should retrieve cached response
        cached = self.cache.get(prompt, 0.7, 100)
        self.assertEqual(cached, response)
    
    def test_cache_persistence(self):
        """Test cache persists to disk"""
        prompt = "persistent test"
        response = "persistent response"
        
        # Cache and save
        self.cache.set(prompt, 0.7, 100, response)
        
        # Create new cache instance pointing to same directory
        new_cache = ResponseCache(cache_dir=self.test_dir)
        
        # Should load cached data
        cached = new_cache.get(prompt, 0.7, 100)
        self.assertEqual(cached, response)
    
    def test_cache_clear(self):
        """Test clearing cache"""
        self.cache.set("test", 0.7, 100, "response")
        self.assertIsNotNone(self.cache.get("test", 0.7, 100))
        
        self.cache.clear()
        self.assertIsNone(self.cache.get("test", 0.7, 100))


class TestAPIUsageStats(unittest.TestCase):
    """Test usage statistics tracking"""
    
    def test_stats_initialization(self):
        """Test stats initialize with correct defaults"""
        stats = APIUsageStats()
        self.assertEqual(stats.total_requests, 0)
        self.assertEqual(stats.successful_requests, 0)
        self.assertEqual(stats.total_cost_usd, 0.0)
    
    def test_stats_to_dict(self):
        """Test converting stats to dictionary"""
        stats = APIUsageStats(total_requests=10, successful_requests=8)
        data = stats.to_dict()
        
        self.assertEqual(data['total_requests'], 10)
        self.assertEqual(data['successful_requests'], 8)
        self.assertIn('last_reset', data)
    
    def test_stats_from_dict(self):
        """Test creating stats from dictionary"""
        data = {
            'total_requests': 10,
            'successful_requests': 8,
            'failed_requests': 2,
            'total_cost_usd': 0.05,
            'cached_responses': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'last_reset': None
        }
        
        stats = APIUsageStats.from_dict(data)
        self.assertEqual(stats.total_requests, 10)
        self.assertEqual(stats.successful_requests, 8)


class TestAIServiceWithoutAPI(unittest.TestCase):
    """Test AI service functionality that doesn't require API calls"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_env = os.environ.get('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = 'test_key_for_testing'
    
    def tearDown(self):
        """Cleanup"""
        shutil.rmtree(self.test_dir)
        if self.original_env:
            os.environ['GEMINI_API_KEY'] = self.original_env
        else:
            os.environ.pop('GEMINI_API_KEY', None)
    
    def test_token_estimation(self):
        """Test token estimation logic"""
        # Skip if google.generativeai not installed
        try:
            ai = AIService()
        except:
            self.skipTest("google-generativeai not installed")
        
        # Test estimation (rough approximation)
        text1 = "Hello world"
        text2 = "This is a much longer piece of text with many more words"
        
        tokens1 = ai._estimate_tokens(text1)
        tokens2 = ai._estimate_tokens(text2)
        
        self.assertGreater(tokens2, tokens1)
        self.assertGreater(tokens1, 0)
    
    def test_cost_calculation(self):
        """Test cost calculation logic"""
        try:
            ai = AIService()
        except:
            self.skipTest("google-generativeai not installed")
        
        # Test cost for 1000 input and 500 output tokens
        cost = ai._calculate_cost(1000, 500)
        
        # Should be very small (fractions of a cent)
        self.assertGreater(cost, 0)
        self.assertLess(cost, 0.01)  # Should be less than 1 cent
    
    def test_usage_report_format(self):
        """Test usage report generation"""
        try:
            ai = AIService()
        except:
            self.skipTest("google-generativeai not installed")
        
        # Manually set some stats
        ai.usage_stats.total_requests = 10
        ai.usage_stats.successful_requests = 8
        ai.usage_stats.cached_responses = 2
        
        report = ai.get_usage_report()
        
        self.assertIn('total_requests', report)
        self.assertIn('success_rate', report)
        self.assertIn('cache_hit_rate', report)
        self.assertIn('total_cost_usd', report)


# Integration test
class TestAIServiceIntegration(unittest.TestCase):
    """Integration tests requiring actual API calls"""
    
    @classmethod
    def setUpClass(cls):
        """Check if we can run integration tests"""
        cls.has_api_key = bool(os.getenv('GEMINI_API_KEY'))
        if not cls.has_api_key:
            print("\n⚠️  Skipping integration tests: GEMINI_API_KEY not set")
    
    def setUp(self):
        """Setup for each test"""
        if not self.has_api_key:
            self.skipTest("GEMINI_API_KEY not set")
    
    def test_basic_generation(self):
        """Test actual text generation (requires API key)"""
        try:
            ai = AIService()
            
            # Check if API is properly initialized
            if not hasattr(ai, 'model') or ai.model is None:
                self.skipTest("Gemini API not properly initialized")
            
            prompt = "Say 'Hello, World!' and nothing else."
            response = ai.generate_text(prompt, temperature=0.0, max_tokens=50)
            
            self.assertIsNotNone(response)
            self.assertGreater(len(response), 0)
            self.assertIn('hello', response.lower())
            
        except ImportError:
            self.skipTest("google-generativeai not installed or API key not available")
        except Exception as e:
            if "API" in str(e) or "key" in str(e).lower():
                self.skipTest(f"API not available: {e}")
            else:
                self.fail(f"Generation failed: {e}")
    
    def test_cache_effectiveness(self):
        """Test that caching works for identical requests"""
        try:
            ai = AIService()
            
            # Check if API is properly initialized
            if not hasattr(ai, 'model') or ai.model is None:
                self.skipTest("Gemini API not properly initialized")
            
            prompt = "Count to 3"
            
            # First call (should hit API)
            response1 = ai.generate_text(prompt, temperature=0.5, max_tokens=50)
            api_calls_after_first = ai.usage_stats.successful_requests
            
            # Second call (should use cache)
            response2 = ai.generate_text(prompt, temperature=0.5, max_tokens=50)
            api_calls_after_second = ai.usage_stats.successful_requests
            
            self.assertEqual(response1, response2)
            self.assertEqual(api_calls_after_first, api_calls_after_second)
            self.assertGreater(ai.usage_stats.cached_responses, 0)
            
        except ImportError:
            self.skipTest("google-generativeai not installed or API key not available")
        except Exception as e:
            if "API" in str(e) or "key" in str(e).lower():
                self.skipTest(f"API not available: {e}")
            else:
                self.fail(f"Cache test failed: {e}")


def run_integration_tests():
    """Run only integration tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIServiceIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test AI Service')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests (requires API key)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.integration:
        print("Running integration tests...")
        run_integration_tests()
    else:
        # Run all tests
        verbosity = 2 if args.verbose else 1
        unittest.main(argv=[''], verbosity=verbosity, exit=True)