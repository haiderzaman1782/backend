"""
Performance benchmark script for Redis caching.

This script measures the performance improvement from Redis caching
by comparing response times with and without cache.

Run with: python tests/benchmark_cache.py
"""

import time
import requests
import statistics
from typing import List, Dict
import json


BASE_URL = "http://localhost:8000"
BOOK_IDS = [1, 2, 3, 4, 5, 10, 20, 50, 100, 200]  # Sample book IDs to test
NUM_ITERATIONS = 10


def measure_response_time(url: str) -> float:
    """
    Measure response time for a single request.
    
    Args:
        url: URL to request
        
    Returns:
        Response time in milliseconds
    """
    start = time.time()
    response = requests.get(url)
    end = time.time()
    
    if response.status_code != 200:
        raise Exception(f"Request failed with status {response.status_code}")
    
    return (end - start) * 1000  # Convert to milliseconds


def benchmark_endpoint(endpoint: str, iterations: int = NUM_ITERATIONS) -> Dict:
    """
    Benchmark an endpoint multiple times.
    
    Args:
        endpoint: Endpoint to benchmark
        iterations: Number of iterations
        
    Returns:
        Dictionary with benchmark results
    """
    times = []
    
    for i in range(iterations):
        try:
            response_time = measure_response_time(f"{BASE_URL}{endpoint}")
            times.append(response_time)
            print(f"  Iteration {i+1}/{iterations}: {response_time:.2f}ms")
        except Exception as e:
            print(f"  Error in iteration {i+1}: {e}")
    
    if not times:
        return {"error": "All requests failed"}
    
    return {
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "samples": len(times)
    }


def clear_cache():
    """Clear all cache before benchmarking."""
    try:
        response = requests.post(f"{BASE_URL}/admin/cache/clear")
        if response.status_code == 200:
            print("✅ Cache cleared successfully")
        else:
            print(f"⚠️ Failed to clear cache: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Could not clear cache: {e}")


def get_cache_stats() -> Dict:
    """Get current cache statistics."""
    try:
        response = requests.get(f"{BASE_URL}/cache/stats")
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        print(f"⚠️ Could not get cache stats: {e}")
        return {}


def benchmark_recommendations():
    """Benchmark recommendation endpoint with and without cache."""
    print("\n" + "="*60)
    print("BENCHMARK: Recommendation Endpoint")
    print("="*60)
    
    book_id = BOOK_IDS[0]
    endpoint = f"/recommend/{book_id}"
    
    # Clear cache first
    print("\n📊 Testing WITHOUT cache (cache miss)...")
    clear_cache()
    time.sleep(1)  # Wait for cache to clear
    
    # First request (cache miss)
    print(f"\nEndpoint: {endpoint}")
    cold_results = benchmark_endpoint(endpoint, iterations=5)
    
    print(f"\n❄️ COLD (Cache Miss) Results:")
    print(f"  Mean: {cold_results['mean']:.2f}ms")
    print(f"  Median: {cold_results['median']:.2f}ms")
    print(f"  Min: {cold_results['min']:.2f}ms")
    print(f"  Max: {cold_results['max']:.2f}ms")
    print(f"  StdDev: {cold_results['stdev']:.2f}ms")
    
    # Subsequent requests (cache hit)
    print(f"\n📊 Testing WITH cache (cache hit)...")
    time.sleep(1)
    
    hot_results = benchmark_endpoint(endpoint, iterations=10)
    
    print(f"\n🔥 HOT (Cache Hit) Results:")
    print(f"  Mean: {hot_results['mean']:.2f}ms")
    print(f"  Median: {hot_results['median']:.2f}ms")
    print(f"  Min: {hot_results['min']:.2f}ms")
    print(f"  Max: {hot_results['max']:.2f}ms")
    print(f"  StdDev: {hot_results['stdev']:.2f}ms")
    
    # Calculate improvement
    improvement = ((cold_results['mean'] - hot_results['mean']) / cold_results['mean']) * 100
    speedup = cold_results['mean'] / hot_results['mean']
    
    print(f"\n📈 Performance Improvement:")
    print(f"  Speed improvement: {improvement:.1f}%")
    print(f"  Speedup factor: {speedup:.1f}x faster")
    print(f"  Time saved: {cold_results['mean'] - hot_results['mean']:.2f}ms per request")


def benchmark_books_list():
    """Benchmark books list endpoint with and without cache."""
    print("\n" + "="*60)
    print("BENCHMARK: Books List Endpoint")
    print("="*60)
    
    endpoint = "/books"
    
    # Clear cache first
    print("\n📊 Testing WITHOUT cache (cache miss)...")
    clear_cache()
    time.sleep(1)
    
    # First request (cache miss)
    print(f"\nEndpoint: {endpoint}")
    cold_results = benchmark_endpoint(endpoint, iterations=5)
    
    print(f"\n❄️ COLD (Cache Miss) Results:")
    print(f"  Mean: {cold_results['mean']:.2f}ms")
    print(f"  Median: {cold_results['median']:.2f}ms")
    
    # Subsequent requests (cache hit)
    print(f"\n📊 Testing WITH cache (cache hit)...")
    time.sleep(1)
    
    hot_results = benchmark_endpoint(endpoint, iterations=10)
    
    print(f"\n🔥 HOT (Cache Hit) Results:")
    print(f"  Mean: {hot_results['mean']:.2f}ms")
    print(f"  Median: {hot_results['median']:.2f}ms")
    
    # Calculate improvement
    improvement = ((cold_results['mean'] - hot_results['mean']) / cold_results['mean']) * 100
    speedup = cold_results['mean'] / hot_results['mean']
    
    print(f"\n📈 Performance Improvement:")
    print(f"  Speed improvement: {improvement:.1f}%")
    print(f"  Speedup factor: {speedup:.1f}x faster")


def benchmark_multiple_books():
    """Benchmark multiple book recommendations."""
    print("\n" + "="*60)
    print("BENCHMARK: Multiple Books (Cache Warming Effect)")
    print("="*60)
    
    clear_cache()
    time.sleep(1)
    
    print(f"\nTesting {len(BOOK_IDS)} different books...")
    
    total_time_cold = 0
    total_time_hot = 0
    
    for book_id in BOOK_IDS:
        endpoint = f"/recommend/{book_id}"
        
        # First request (cold)
        try:
            cold_time = measure_response_time(f"{BASE_URL}{endpoint}")
            total_time_cold += cold_time
            
            # Second request (hot)
            hot_time = measure_response_time(f"{BASE_URL}{endpoint}")
            total_time_hot += hot_time
            
            print(f"  Book {book_id}: {cold_time:.2f}ms → {hot_time:.2f}ms")
        except Exception as e:
            print(f"  Book {book_id}: Error - {e}")
    
    print(f"\n📊 Total Time:")
    print(f"  Without cache: {total_time_cold:.2f}ms")
    print(f"  With cache: {total_time_hot:.2f}ms")
    print(f"  Time saved: {total_time_cold - total_time_hot:.2f}ms")
    print(f"  Improvement: {((total_time_cold - total_time_hot) / total_time_cold * 100):.1f}%")


def main():
    """Run all benchmarks."""
    print("\n🚀 Redis Cache Performance Benchmark")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server is not responding. Please start the FastAPI server.")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Please start the server with: uvicorn main:app --reload")
        return
    
    # Check Redis status
    try:
        response = requests.get(f"{BASE_URL}/health/redis")
        redis_health = response.json()
        if redis_health.get("status") != "healthy":
            print("⚠️ Redis is not healthy. Results may not show caching benefits.")
            print(f"   Status: {redis_health}")
        else:
            print(f"✅ Redis is healthy (version {redis_health.get('version')})")
    except Exception as e:
        print(f"⚠️ Could not check Redis health: {e}")
    
    # Run benchmarks
    benchmark_recommendations()
    benchmark_books_list()
    benchmark_multiple_books()
    
    # Show final cache stats
    print("\n" + "="*60)
    print("FINAL CACHE STATISTICS")
    print("="*60)
    stats = get_cache_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Benchmark completed!")


if __name__ == "__main__":
    main()
