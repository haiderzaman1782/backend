"""
Unit tests for Redis cache service.

Run with: pytest tests/test_cache_service.py
"""

import pytest
import json
from unittest.mock import Mock, patch
from backend.cache_service import (
    get_cached_recommendations,
    set_cached_recommendations,
    invalidate_recommendations,
    get_cached_books,
    set_cached_books,
    invalidate_books_list,
    get_cache_stats,
    clear_all_cache,
    get_all_cache_keys
)


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    with patch('backend.cache_service.redis_client') as mock:
        mock.is_available = True
        mock.client = Mock()
        yield mock


class TestRecommendationsCache:
    """Test recommendation caching functions."""
    
    def test_get_cached_recommendations_hit(self, mock_redis_client):
        """Test cache hit for recommendations."""
        book_id = 1
        expected_data = {
            "book_id": 1,
            "recommendations": [{"title": "Test Book"}]
        }
        
        mock_redis_client.client.get.return_value = json.dumps(expected_data)
        mock_redis_client.client.incr.return_value = None
        
        result = get_cached_recommendations(book_id)
        
        assert result == expected_data
        mock_redis_client.client.get.assert_called_once_with("book:recommendations:1")
        mock_redis_client.client.incr.assert_called_once_with("stats:cache:hits")
    
    def test_get_cached_recommendations_miss(self, mock_redis_client):
        """Test cache miss for recommendations."""
        book_id = 1
        mock_redis_client.client.get.return_value = None
        
        result = get_cached_recommendations(book_id)
        
        assert result is None
        mock_redis_client.client.incr.assert_called_once_with("stats:cache:misses")
    
    def test_set_cached_recommendations(self, mock_redis_client):
        """Test setting recommendations in cache."""
        book_id = 1
        data = {"book_id": 1, "recommendations": []}
        ttl = 3600
        
        mock_redis_client.client.setex.return_value = True
        
        result = set_cached_recommendations(book_id, data, ttl)
        
        assert result is True
        mock_redis_client.client.setex.assert_called_once()
        args = mock_redis_client.client.setex.call_args[0]
        assert args[0] == "book:recommendations:1"
        assert args[1] == ttl
        assert json.loads(args[2]) == data
    
    def test_invalidate_recommendations(self, mock_redis_client):
        """Test invalidating recommendation cache."""
        book_id = 1
        mock_redis_client.client.delete.return_value = 1
        
        result = invalidate_recommendations(book_id)
        
        assert result is True
        mock_redis_client.client.delete.assert_called_once_with("book:recommendations:1")


class TestBooksListCache:
    """Test books list caching functions."""
    
    def test_get_cached_books_hit(self, mock_redis_client):
        """Test cache hit for books list."""
        expected_data = [{"id": 1, "title": "Book 1"}]
        
        mock_redis_client.client.get.return_value = json.dumps(expected_data)
        mock_redis_client.client.incr.return_value = None
        
        result = get_cached_books()
        
        assert result == expected_data
        mock_redis_client.client.get.assert_called_once_with("book:list:all")
    
    def test_set_cached_books(self, mock_redis_client):
        """Test setting books list in cache."""
        data = [{"id": 1, "title": "Book 1"}]
        ttl = 300
        
        mock_redis_client.client.setex.return_value = True
        
        result = set_cached_books(data, ttl)
        
        assert result is True
        mock_redis_client.client.setex.assert_called_once()
    
    def test_invalidate_books_list(self, mock_redis_client):
        """Test invalidating books list cache."""
        mock_redis_client.client.delete.return_value = 1
        
        result = invalidate_books_list()
        
        assert result is True
        mock_redis_client.client.delete.assert_called_once_with("book:list:all")


class TestCacheManagement:
    """Test cache management functions."""
    
    def test_get_cache_stats(self, mock_redis_client):
        """Test getting cache statistics."""
        mock_redis_client.client.get.side_effect = ["100", "50"]
        
        result = get_cache_stats()
        
        assert result["status"] == "available"
        assert result["hits"] == 100
        assert result["misses"] == 50
        assert result["total_requests"] == 150
        assert result["hit_rate"] == 66.67
    
    def test_get_cache_stats_unavailable(self):
        """Test cache stats when Redis is unavailable."""
        with patch('backend.cache_service.redis_client') as mock:
            mock.is_available = False
            
            result = get_cache_stats()
            
            assert result["status"] == "unavailable"
            assert result["hits"] == 0
            assert result["misses"] == 0
    
    def test_clear_all_cache(self, mock_redis_client):
        """Test clearing all cache."""
        mock_redis_client.client.flushdb.return_value = True
        
        result = clear_all_cache()
        
        assert result is True
        mock_redis_client.client.flushdb.assert_called_once()
    
    def test_get_all_cache_keys(self, mock_redis_client):
        """Test getting all cache keys."""
        expected_keys = ["book:recommendations:1", "book:list:all"]
        mock_redis_client.client.keys.return_value = expected_keys
        
        result = get_all_cache_keys()
        
        assert result == expected_keys
        mock_redis_client.client.keys.assert_called_once_with("*")


class TestErrorHandling:
    """Test error handling in cache operations."""
    
    def test_get_cache_with_redis_unavailable(self):
        """Test cache get when Redis is unavailable."""
        with patch('backend.cache_service.redis_client') as mock:
            mock.is_available = False
            
            result = get_cached_recommendations(1)
            
            assert result is None
    
    def test_set_cache_with_redis_unavailable(self):
        """Test cache set when Redis is unavailable."""
        with patch('backend.cache_service.redis_client') as mock:
            mock.is_available = False
            
            result = set_cached_recommendations(1, {})
            
            assert result is False
    
    def test_get_cache_with_exception(self, mock_redis_client):
        """Test cache get with exception."""
        mock_redis_client.client.get.side_effect = Exception("Redis error")
        
        result = get_cached_recommendations(1)
        
        assert result is None
    
    def test_set_cache_with_exception(self, mock_redis_client):
        """Test cache set with exception."""
        mock_redis_client.client.setex.side_effect = Exception("Redis error")
        
        result = set_cached_recommendations(1, {})
        
        assert result is False
