"""
Geo Data Provider
IP geolocation and geographic visualization data
"""
import os
import sys
import json
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import LOGS_DIR, DATABASE_URL

# Cache for IP geolocation results
GEO_CACHE_FILE = LOGS_DIR / "geo_cache.json"
CONNECTIONS_LOG_FILE = LOGS_DIR / "connections.jsonl"

# Free IP geolocation API
GEO_API_URL = "http://ip-api.com/json/{ip}"


def _load_geo_cache() -> Dict[str, Dict]:
    """Load geolocation cache"""
    if GEO_CACHE_FILE.exists():
        try:
            with open(GEO_CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def _save_geo_cache(cache: Dict[str, Dict]):
    """Save geolocation cache"""
    LOGS_DIR.mkdir(exist_ok=True)
    with open(GEO_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def get_ip_location(ip: str) -> Optional[Dict[str, Any]]:
    """
    Get geolocation for an IP address
    Uses ip-api.com (free, 45 req/min limit)
    """
    # Skip private/local IPs
    if ip.startswith(('127.', '192.168.', '10.', '172.16.', '172.17.', '172.18.', 
                      '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                      '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
                      '172.29.', '172.30.', '172.31.', 'localhost', '0.0.0.0')):
        return {
            "ip": ip,
            "country": "Local",
            "countryCode": "LO",
            "city": "Local Network",
            "lat": 0,
            "lon": 0,
            "isp": "Private Network",
            "status": "local"
        }
    
    # Check cache first
    cache = _load_geo_cache()
    if ip in cache:
        cached = cache[ip]
        # Check if cache is less than 7 days old
        if cached.get("cached_at"):
            cached_time = datetime.fromisoformat(cached["cached_at"])
            if datetime.now() - cached_time < timedelta(days=7):
                return cached
    
    # Query API
    try:
        response = httpx.get(GEO_API_URL.format(ip=ip), timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                result = {
                    "ip": ip,
                    "country": data.get("country", "Unknown"),
                    "countryCode": data.get("countryCode", "XX"),
                    "region": data.get("regionName", ""),
                    "city": data.get("city", "Unknown"),
                    "lat": data.get("lat", 0),
                    "lon": data.get("lon", 0),
                    "isp": data.get("isp", ""),
                    "org": data.get("org", ""),
                    "timezone": data.get("timezone", ""),
                    "status": "success",
                    "cached_at": datetime.now().isoformat()
                }
                
                # Update cache
                cache[ip] = result
                _save_geo_cache(cache)
                
                return result
    except Exception as e:
        print(f"Geolocation lookup failed for {ip}: {e}")
    
    return {
        "ip": ip,
        "country": "Unknown",
        "countryCode": "XX",
        "city": "Unknown",
        "lat": 0,
        "lon": 0,
        "status": "failed"
    }


def log_connection(ip: str, endpoint: str = "", user_agent: str = "", 
                   user: str = "", status: str = "success"):
    """Log a connection for geographic tracking"""
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Get geolocation
    geo = get_ip_location(ip)
    
    connection = {
        "timestamp": datetime.now().isoformat(),
        "ip": ip,
        "endpoint": endpoint,
        "user_agent": user_agent,
        "user": user,
        "status": status,
        "geo": geo
    }
    
    with open(CONNECTIONS_LOG_FILE, 'a') as f:
        f.write(json.dumps(connection) + "\n")
    
    return connection


def get_connections(limit: int = 500) -> List[Dict[str, Any]]:
    """Get recent connections with geo data"""
    if not CONNECTIONS_LOG_FILE.exists():
        return []
    
    connections = []
    with open(CONNECTIONS_LOG_FILE, 'r') as f:
        for line in f:
            try:
                connections.append(json.loads(line.strip()))
            except:
                continue
    
    return list(reversed(connections[-limit:]))


def get_connection_map_data() -> Dict[str, Any]:
    """Get data formatted for Plotly geo scatter map"""
    connections = get_connections(1000)
    
    # Aggregate by location
    locations = defaultdict(lambda: {"count": 0, "ips": set(), "last_seen": ""})
    
    for conn in connections:
        geo = conn.get("geo", {})
        if geo.get("lat") and geo.get("lon"):
            key = (geo["lat"], geo["lon"], geo.get("city", "Unknown"))
            locations[key]["count"] += 1
            locations[key]["ips"].add(conn.get("ip", ""))
            locations[key]["last_seen"] = conn.get("timestamp", "")
            locations[key]["country"] = geo.get("country", "Unknown")
            locations[key]["city"] = geo.get("city", "Unknown")
    
    # Format for Plotly
    lats = []
    lons = []
    sizes = []
    texts = []
    colors = []
    
    for (lat, lon, city), data in locations.items():
        lats.append(lat)
        lons.append(lon)
        sizes.append(min(50, 10 + data["count"] * 2))  # Size based on connection count
        texts.append(f"{city}, {data['country']}<br>Connections: {data['count']}<br>Unique IPs: {len(data['ips'])}")
        colors.append(data["count"])
    
    return {
        "lats": lats,
        "lons": lons,
        "sizes": sizes,
        "texts": texts,
        "colors": colors,
        "total_locations": len(locations),
        "total_connections": len(connections)
    }


def get_connection_stats() -> Dict[str, Any]:
    """Get connection statistics by country/city"""
    connections = get_connections(1000)
    
    by_country = defaultdict(int)
    by_city = defaultdict(int)
    by_hour = defaultdict(int)
    
    for conn in connections:
        geo = conn.get("geo", {})
        by_country[geo.get("country", "Unknown")] += 1
        by_city[f"{geo.get('city', 'Unknown')}, {geo.get('countryCode', 'XX')}"] += 1
        
        try:
            hour = datetime.fromisoformat(conn["timestamp"]).hour
            by_hour[hour] += 1
        except:
            pass
    
    # Sort and get top entries
    top_countries = sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10]
    top_cities = sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "top_countries": [{"country": c, "count": n} for c, n in top_countries],
        "top_cities": [{"city": c, "count": n} for c, n in top_cities],
        "by_hour": dict(by_hour),
        "total_connections": len(connections)
    }


# =============================================================================
# DJANGO INTEGRATION DATA
# =============================================================================

def get_django_endpoint_stats() -> Dict[str, Any]:
    """Get Django API endpoint usage statistics"""
    # Read from Django log file if available
    django_log = LOGS_DIR / "django_requests.jsonl"
    
    if not django_log.exists():
        return {"endpoints": [], "total_requests": 0}
    
    requests = []
    with open(django_log, 'r') as f:
        for line in f:
            try:
                requests.append(json.loads(line.strip()))
            except:
                continue
    
    # Aggregate by endpoint
    endpoints = defaultdict(lambda: {"count": 0, "avg_time": 0, "errors": 0, "times": []})
    
    for req in requests:
        path = req.get("path", "/")
        endpoints[path]["count"] += 1
        endpoints[path]["times"].append(req.get("response_time_ms", 0))
        if req.get("status_code", 200) >= 400:
            endpoints[path]["errors"] += 1
    
    # Calculate averages
    result = []
    for path, data in endpoints.items():
        avg_time = sum(data["times"]) / len(data["times"]) if data["times"] else 0
        result.append({
            "endpoint": path,
            "requests": data["count"],
            "avg_response_ms": round(avg_time, 2),
            "errors": data["errors"],
            "error_rate": round(data["errors"] / data["count"] * 100, 1) if data["count"] > 0 else 0
        })
    
    # Sort by request count
    result.sort(key=lambda x: x["requests"], reverse=True)
    
    return {
        "endpoints": result[:20],
        "total_requests": len(requests),
        "total_endpoints": len(endpoints)
    }


def get_active_sessions() -> List[Dict[str, Any]]:
    """Get active user sessions (simulated from recent connections)"""
    connections = get_connections(100)
    
    # Group by user/IP
    sessions = {}
    for conn in connections:
        key = conn.get("user") or conn.get("ip", "unknown")
        if key not in sessions:
            sessions[key] = {
                "user": conn.get("user", "anonymous"),
                "ip": conn.get("ip", ""),
                "last_activity": conn.get("timestamp", ""),
                "requests": 0,
                "location": conn.get("geo", {}).get("city", "Unknown")
            }
        sessions[key]["requests"] += 1
        if conn.get("timestamp", "") > sessions[key]["last_activity"]:
            sessions[key]["last_activity"] = conn["timestamp"]
    
    # Filter to recent (last 30 min)
    cutoff = datetime.now() - timedelta(minutes=30)
    active = []
    for session in sessions.values():
        try:
            if datetime.fromisoformat(session["last_activity"]) > cutoff:
                active.append(session)
        except:
            pass
    
    return sorted(active, key=lambda x: x["last_activity"], reverse=True)


# =============================================================================
# SAMPLE DATA
# =============================================================================

def seed_sample_geo_data():
    """Generate sample geographic data for testing"""
    sample_ips = [
        ("8.8.8.8", "/api/proposals/", "user1"),
        ("1.1.1.1", "/api/donations/", "user2"),
        ("208.67.222.222", "/api/rounds/", "admin"),
        ("9.9.9.9", "/api/wallets/", "user3"),
        ("185.228.168.9", "/api/proposals/", "user1"),
        ("76.76.2.0", "/api/donations/", "user4"),
        ("94.140.14.14", "/api/rounds/", "user5"),
    ]
    
    for ip, endpoint, user in sample_ips:
        log_connection(ip, endpoint, "Mozilla/5.0", user, "success")
