"""
AI Module - Google Gemini Integration
Week 1: Infrastructure Setup
"""

from .ai_service import (
    AIService,
    RateLimiter,
    ResponseCache,
    APIUsageStats,
    get_ai_service,
    initialize_ai_service
)

__all__ = [
    'AIService',
    'RateLimiter',
    'ResponseCache',
    'APIUsageStats',
    'get_ai_service',
    'initialize_ai_service'
]

__version__ = '1.0.0'