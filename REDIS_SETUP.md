# Redis Setup Guide

This guide will help you set up Redis for local development with the Book Recommendation System.

## What is Redis?

Redis is an in-memory data store used for caching. It dramatically improves API performance by storing frequently accessed data in memory, reducing database queries and computation time.

## Installation

### Windows

#### Option 1: Using Windows Subsystem for Linux (WSL) - Recommended

1. **Install WSL** (if not already installed):
   ```powershell
   wsl --install
   ```

2. **Install Redis in WSL**:
   ```bash
   sudo apt update
   sudo apt install redis-server
   ```

3. **Start Redis**:
   ```bash
   sudo service redis-server start
   ```

4. **Verify Redis is running**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

#### Option 2: Using Docker - Easiest

1. **Install Docker Desktop** from [docker.com](https://www.docker.com/products/docker-desktop)

2. **Run Redis container**:
   ```powershell
   docker run -d --name redis-cache -p 6379:6379 redis:latest
   ```

3. **Verify Redis is running**:
   ```powershell
   docker exec -it redis-cache redis-cli ping
   # Should return: PONG
   ```

4. **To stop Redis**:
   ```powershell
   docker stop redis-cache
   ```

5. **To start Redis again**:
   ```powershell
   docker start redis-cache
   ```

#### Option 3: Using Memurai (Windows Native)

1. **Download Memurai** from [memurai.com](https://www.memurai.com/)
2. **Install and run** the installer
3. **Memurai runs as a Windows service** automatically

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server

# Enable Redis to start on boot
sudo systemctl enable redis-server

# Verify
redis-cli ping
```

### macOS

```bash
# Using Homebrew
brew install redis

# Start Redis
brew services start redis

# Verify
redis-cli ping
```

## Configuration

### Environment Variables

Update your `.env` file in the `Book-Backend` directory:

```env
# Redis Configuration (Local Development)
REDIS_URL=redis://localhost:6379/0

# Cache TTL Settings (in seconds)
CACHE_TTL_RECOMMENDATIONS=3600  # 1 hour
CACHE_TTL_BOOKS=300             # 5 minutes
CACHE_TTL_BOOK_DETAIL=1800      # 30 minutes
```

### Connection Test

After starting Redis, test the connection:

```bash
# In your terminal
redis-cli

# Inside redis-cli
127.0.0.1:6379> ping
PONG
127.0.0.1:6379> set test "Hello Redis"
OK
127.0.0.1:6379> get test
"Hello Redis"
127.0.0.1:6379> exit
```

## Installing Python Dependencies

Install the Redis Python packages:

```bash
cd Book-Backend
pip install -r requirements.txt
```

This will install:
- `redis>=5.0.0` - Python Redis client
- `hiredis>=2.2.0` - High-performance C parser for Redis

## Running the Application

1. **Start Redis** (using one of the methods above)

2. **Start the FastAPI server**:
   ```bash
   cd Book-Backend
   uvicorn main:app --reload
   ```

3. **Check the logs** - You should see:
   ```
   ✅ Redis connection established successfully
   🚀 Starting application...
   🔥 Warming cache with popular books...
   ✅ Cache warming completed
   ```

## Testing Redis Integration

### 1. Health Check

Visit: `http://localhost:8000/health/redis`

Expected response:
```json
{
  "status": "healthy",
  "version": "7.x.x",
  "connected_clients": 1,
  "used_memory_human": "1.23M",
  "uptime_in_seconds": 12345
}
```

### 2. Cache Statistics

Visit: `http://localhost:8000/cache/stats`

Expected response:
```json
{
  "status": "available",
  "hits": 10,
  "misses": 5,
  "total_requests": 15,
  "hit_rate": 66.67
}
```

### 3. Test Caching Performance

**First request** (cache miss):
```bash
curl http://localhost:8000/recommend/1
# Check response time - should be ~50-100ms
```

**Second request** (cache hit):
```bash
curl http://localhost:8000/recommend/1
# Check response time - should be ~5-10ms (much faster!)
```

### 4. View Cache Keys

Visit: `http://localhost:8000/admin/cache/keys`

You'll see keys like:
```json
{
  "total_keys": 12,
  "keys": [
    "book:recommendations:1",
    "book:recommendations:2",
    "book:list:all",
    "stats:cache:hits",
    "stats:cache:misses"
  ]
}
```

## Admin Endpoints

The following admin endpoints are available for cache management:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/cache/stats` | GET | View cache statistics |
| `/admin/cache/clear` | POST | Clear all cache |
| `/admin/cache/keys` | GET | List all cache keys |
| `/admin/cache/book/{book_id}` | DELETE | Invalidate specific book cache |
| `/admin/cache/invalidate/books` | POST | Invalidate books list cache |
| `/admin/cache/reconnect` | POST | Reconnect to Redis |

## Monitoring Cache in Real-Time

### Using Redis CLI

```bash
# Monitor all commands in real-time
redis-cli monitor

# View all keys
redis-cli keys "*"

# Check TTL of a key
redis-cli ttl "book:recommendations:1"

# Get value of a key
redis-cli get "book:recommendations:1"

# View memory usage
redis-cli info memory
```

### Using Redis Desktop Manager (GUI)

Download a Redis GUI client for easier visualization:
- **RedisInsight** (Official, Free): [redis.com/redis-enterprise/redis-insight](https://redis.com/redis-enterprise/redis-insight/)
- **Another Redis Desktop Manager**: [github.com/qishibo/AnotherRedisDesktopManager](https://github.com/qishibo/AnotherRedisDesktopManager)

## Troubleshooting

### Redis Connection Failed

**Error**: `⚠️ Redis connection failed: Error connecting to localhost:6379`

**Solutions**:
1. Make sure Redis is running:
   ```bash
   # WSL
   sudo service redis-server status
   
   # Docker
   docker ps | grep redis
   
   # Linux
   sudo systemctl status redis-server
   ```

2. Check if port 6379 is in use:
   ```bash
   netstat -an | findstr 6379
   ```

3. Try connecting manually:
   ```bash
   redis-cli ping
   ```

### Application Runs Without Redis

The application is designed to work even if Redis is unavailable. You'll see:
```
⚠️ Redis not available, skipping cache warming
```

The API will continue to work, but without caching benefits.

### Cache Not Working

1. **Check Redis connection**:
   ```bash
   curl http://localhost:8000/health/redis
   ```

2. **View cache stats**:
   ```bash
   curl http://localhost:8000/cache/stats
   ```

3. **Clear cache and retry**:
   ```bash
   curl -X POST http://localhost:8000/admin/cache/clear
   ```

### Performance Not Improving

1. **Verify cache is being used** - Check logs for "Cache HIT" messages
2. **Check cache hit rate** - Visit `/cache/stats`, should be >50% after warming
3. **Increase cache TTL** - Modify TTL values in `.env`

## Performance Benchmarks

Expected performance improvements with Redis:

| Metric | Without Redis | With Redis | Improvement |
|--------|--------------|------------|-------------|
| `/recommend/{id}` | 50-100ms | 5-10ms | **90% faster** |
| `/books` | 200-500ms | 10-20ms | **95% faster** |
| Database queries | 100% | 20-50% | **50-80% reduction** |
| Concurrent users | 10-20 | 30-60 | **2-3x capacity** |

## Cache Key Naming Convention

The application uses a hierarchical naming scheme:

- `book:recommendations:{book_id}` - Cached recommendations for a book
- `book:list:all` - Cached list of all books
- `book:detail:{book_id}` - Cached individual book details
- `stats:cache:hits` - Cache hit counter
- `stats:cache:misses` - Cache miss counter

## Next Steps

1. ✅ Install Redis locally
2. ✅ Update `.env` with Redis configuration
3. ✅ Install Python dependencies
4. ✅ Start the application
5. ✅ Test cache performance
6. ✅ Monitor cache statistics

## Production Deployment

For production, consider using managed Redis services:
- **Redis Cloud** (redis.com/cloud)
- **AWS ElastiCache**
- **Azure Cache for Redis**
- **Google Cloud Memorystore**
- **Upstash** (Serverless Redis)

Update `REDIS_URL` in production `.env`:
```env
REDIS_URL=redis://username:password@your-redis-host:port/0
```

## Additional Resources

- [Redis Documentation](https://redis.io/docs/)
- [Redis Python Client](https://redis-py.readthedocs.io/)
- [FastAPI Caching Best Practices](https://fastapi.tiangolo.com/)
