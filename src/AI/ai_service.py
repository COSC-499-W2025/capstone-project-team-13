"""
AI Service Module - Gemini 2.5 Flash Integration

Features:
- Gemini API integration with safety settings
- Rate limiting and request throttling
- Response caching to minimize API usage
- Cost tracking and usage monitoring
- Comprehensive error handling
- Token estimation for cost management
"""

import os
import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from collections import deque
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from pathlib import Path

# Find .env in project root (go up from src/AI/)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# DEBUG: Check if key loaded
api_key_check = os.getenv('GEMINI_API_KEY')
if api_key_check:
    print(f"✅ API key loaded: {api_key_check[:10]}...")
else:
    print("❌ API key NOT loaded from .env")

try:
    import google.generativeai as genai
except ImportError:
    print("⚠️  google-generativeai not installed. Run: pip install google-generativeai")
    genai = None


@dataclass
class APIUsageStats:
    """Track API usage statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_responses: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    last_reset: datetime = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['last_reset'] = self.last_reset.isoformat() if self.last_reset else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'APIUsageStats':
        if data.get('last_reset'):
            data['last_reset'] = datetime.fromisoformat(data['last_reset'])
        return cls(**data)


class RateLimiter:
    """Token bucket rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int = 15):
        """
        Initialize rate limiter
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.request_times = deque()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove requests older than 1 minute
        while self.request_times and self.request_times[0] < now - 60:
            self.request_times.popleft()
        
        # If at limit, wait
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                print(f"⏳ Rate limit reached. Waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(time.time())


class ResponseCache:
    """Cache AI responses to minimize API usage"""
    
    def __init__(self, cache_dir: str = "data/ai_cache"):
        """Initialize cache with persistent storage"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "response_cache.json"
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save cache: {e}")
    
    def get_cache_key(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate unique cache key for a request"""
        key_string = f"{prompt}|{temperature}|{max_tokens}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Get cached response if available"""
        cache_key = self.get_cache_key(prompt, temperature, max_tokens)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            # Check if cache entry is less than 7 days old
            cache_time = datetime.fromisoformat(cached['timestamp'])
            if datetime.now() - cache_time < timedelta(days=7):
                return cached['response']
        return None
    
    def set(self, prompt: str, temperature: float, max_tokens: int, response: str):
        """Cache a response"""
        cache_key = self.get_cache_key(prompt, temperature, max_tokens)
        self.cache[cache_key] = {
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
    
    def clear(self):
        """Clear all cached responses"""
        self.cache = {}
        self._save_cache()


class AIService:
    """
    Centralized AI service using Google Gemini 2.5 Flash
    """
    
    # Gemini 2.5 Flash pricing (per 1M tokens)
    INPUT_COST_PER_1M = 0.075
    OUTPUT_COST_PER_1M = 0.30
    
    def __init__(
    self,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.0-flash-exp",
    requests_per_minute: int = 15,
    enable_cache: bool = True
    ):
        """
        Initialize AI service
        
        Args:
            api_key: Gemini API key
            model_name: Model to use (default: gemini-2.0-flash-exp)
            requests_per_minute: Rate limit
            enable_cache: Whether to cache responses
        """
        if genai is None:
            raise RuntimeError("google-generativeai package not installed")
        
        # Get API key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        
        # Initialize components
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.cache = ResponseCache() if enable_cache else None
        
        # Load or initialize usage stats
        self.stats_file = Path("data/ai_usage_stats.json")
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        self.usage_stats = self._load_stats()
        
        # Create model instance - FIXED: Using default safety settings
        self.model = genai.GenerativeModel(model_name=self.model_name)
        
        print(f"✓ AI Service initialized with {self.model_name}")
            
        
    
    def _load_stats(self) -> APIUsageStats:
        """Load usage statistics from disk"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    return APIUsageStats.from_dict(data)
            except Exception:
                pass
        return APIUsageStats(last_reset=datetime.now())
    
    def _save_stats(self):
        """Save usage statistics to disk"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.usage_stats.to_dict(), f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save stats: {e}")
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (more accurate would require tokenizer)
        Rule of thumb: ~4 characters per token for English
        """
        return len(text) // 4
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for a request"""
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        return input_cost + output_cost
    
    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Generate text using Gemini
        
        Args:
            prompt: Input prompt
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum response length
            use_cache: Whether to use cached responses
            
        Returns:
            Generated text or None if failed
        """
        try:
            # Check cache first
            if use_cache and self.cache:
                cached = self.cache.get(prompt, temperature, max_tokens)
                if cached:
                    self.usage_stats.cached_responses += 1
                    print("✓ Using cached response")
                    return cached
            
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Track request
            self.usage_stats.total_requests += 1
            
            # Estimate input tokens
            input_tokens = self._estimate_tokens(prompt)
            self.usage_stats.total_input_tokens += input_tokens
            
            # Generate response
            print(f"🤖 Calling Gemini API... (est. {input_tokens} input tokens)")
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            # Extract text
            if not response or not response.text:
                raise ValueError("Empty response from API")
            
            result_text = response.text.strip()
            
            # Track output tokens
            output_tokens = self._estimate_tokens(result_text)
            self.usage_stats.total_output_tokens += output_tokens
            
            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)
            self.usage_stats.total_cost_usd += cost
            
            # Update stats
            self.usage_stats.successful_requests += 1
            self._save_stats()
            
            # Cache response
            if use_cache and self.cache:
                self.cache.set(prompt, temperature, max_tokens, result_text)
            
            print(f"✓ Response received (~{output_tokens} tokens")
            
            return result_text
            
        except Exception as e:
            self.usage_stats.failed_requests += 1
            self._save_stats()
            print(f"✗ AI generation failed: {e}")
            return None
    
    def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> Optional[str]:
        """
        Generate text with automatic retry on failure
        
        Args:
            prompt: Input prompt
            max_retries: Maximum retry attempts
            **kwargs: Additional arguments for generate_text
            
        Returns:
            Generated text or None if all retries failed
        """
        for attempt in range(max_retries):
            result = self.generate_text(prompt, **kwargs)
            if result:
                return result
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                print(f"⏳ Retry {attempt + 1}/{max_retries} in {wait_time}s...")
                time.sleep(wait_time)
        
        print(f"✗ All {max_retries} attempts failed")
        return None
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        total_tokens = self.usage_stats.total_input_tokens + self.usage_stats.total_output_tokens
        
        return {
            'total_requests': self.usage_stats.total_requests,
            'successful': self.usage_stats.successful_requests,
            'failed': self.usage_stats.failed_requests,
            'cached': self.usage_stats.cached_responses,
            'success_rate': f"{(self.usage_stats.successful_requests / max(self.usage_stats.total_requests, 1)) * 100:.1f}%",
            'cache_hit_rate': f"{(self.usage_stats.cached_responses / max(self.usage_stats.total_requests, 1)) * 100:.1f}%",
            'total_tokens': total_tokens,
            'input_tokens': self.usage_stats.total_input_tokens,
            'output_tokens': self.usage_stats.total_output_tokens,
            'total_cost_usd': f"${self.usage_stats.total_cost_usd:.4f}",
            'avg_cost_per_request': f"${self.usage_stats.total_cost_usd / max(self.usage_stats.successful_requests, 1):.4f}",
            'last_reset': self.usage_stats.last_reset.strftime('%Y-%m-%d %H:%M:%S') if self.usage_stats.last_reset else 'Never'
        }
    
    def print_usage_report(self):
        """Print formatted usage report"""
        report = self.get_usage_report()
        
        print("\n" + "="*60)
        print("AI SERVICE USAGE REPORT")
        print("="*60)
        print(f"\n📊 Request Statistics:")
        print(f"  Total Requests: {report['total_requests']}")
        print(f"  Successful: {report['successful']} ({report['success_rate']})")
        print(f"  Failed: {report['failed']}")
        print(f"  Cached Responses: {report['cached']} ({report['cache_hit_rate']})")
        
        print(f"\n💬 Token Usage:")
        print(f"  Total Tokens: {report['total_tokens']:,}")
        print(f"  Input Tokens: {report['input_tokens']:,}")
        print(f"  Output Tokens: {report['output_tokens']:,}")
        
        print(f"\n💰 Cost Analysis:")
        print(f"  Total Cost: {report['total_cost_usd']}")
        print(f"  Avg Cost/Request: {report['avg_cost_per_request']}")
        
        print(f"\n🕐 Last Reset: {report['last_reset']}")
        print("="*60 + "\n")
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.usage_stats = APIUsageStats(last_reset=datetime.now())
        self._save_stats()
        print("✓ Usage statistics reset")
    
    def clear_cache(self):
        """Clear response cache"""
        if self.cache:
            self.cache.clear()
            print("✓ Response cache cleared")


# Global AI service instance (lazy initialization)
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create global AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def initialize_ai_service(api_key: Optional[str] = None, **kwargs) -> AIService:
    """
    Initialize global AI service with custom settings
    
    Args:
        api_key: Gemini API key
        **kwargs: Additional arguments for AIService
        
    Returns:
        Initialized AIService instance
    """
    global _ai_service
    _ai_service = AIService(api_key=api_key, **kwargs)
    return _ai_service


# Example usage functions for testing
def test_basic_generation():
    """Test basic text generation"""
    print("\n" + "="*60)
    print("TEST: Basic Text Generation")
    print("="*60 + "\n")
    
    ai = get_ai_service()
    
    prompt = "In 2-3 sentences, explain what a capstone project is for university students."
    print(f"Prompt: {prompt}\n")
    
    response = ai.generate_text(prompt, temperature=0.5, max_tokens=150)
    
    if response:
        print(f"\nResponse:\n{response}\n")
        return True
    return False


def test_project_summary():
    """Test generating a project summary"""
    print("\n" + "="*60)
    print("TEST: Project Summary Generation")
    print("="*60 + "\n")
    
    ai = get_ai_service()
    
    # Minimal project data to test
    project_data = {
        "name": "Weather Dashboard",
        "languages": ["Python", "JavaScript"],
        "frameworks": ["Flask", "React"],
        "lines_of_code": 1500,
        "file_count": 12
    }
    
    prompt = f"""Generate a brief 2-sentence professional summary for this coding project:

Project: {project_data['name']}
Languages: {', '.join(project_data['languages'])}
Frameworks: {', '.join(project_data['frameworks'])}
Size: {project_data['lines_of_code']} lines of code across {project_data['file_count']} files

Summary:"""
    
    print(f"Project: {project_data['name']}")
    print(f"Tech Stack: {', '.join(project_data['languages'])} with {', '.join(project_data['frameworks'])}\n")
    
    response = ai.generate_with_retry(prompt, temperature=0.7, max_tokens=200)
    
    if response:
        print(f"AI-Generated Summary:\n{response}\n")
        return True
    return False


if __name__ == "__main__":
    """Test the AI service"""
    
    print("🤖 AI Service Module - Week 1 Tests")
    print("="*60)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded .env file\n")
    except ImportError:
        print("⚠️  python-dotenv not installed (optional)\n")
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n❌ GEMINI_API_KEY environment variable not set!")
        print("\nTo set it:")
        print("  Windows: set GEMINI_API_KEY=your_key_here")
        print("  Linux/Mac: export GEMINI_API_KEY=your_key_here")
        print("\nGet your API key from: https://makersuite.google.com/app/apikey")
        exit(1)
    
    try:
        # Initialize service
        ai = initialize_ai_service()
        
        # Run tests
        print("\n📝 Running Tests...\n")
        
        test1 = test_basic_generation()
        test2 = test_project_summary()
        
        # Print usage report
        ai.print_usage_report()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✓ Basic Generation: {'PASSED' if test1 else 'FAILED'}")
        print(f"✓ Project Summary: {'PASSED' if test2 else 'FAILED'}")
        print("="*60 + "\n")
        
        if test1 and test2:
            print("✅ All tests passed! AI service is ready to use.")
        else:
            print("⚠️  Some tests failed. Check the output above.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)