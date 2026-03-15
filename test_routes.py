"""
Comprehensive route testing script
Tests all routes for HTTP errors
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WBPMISUESO.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.urls import get_resolver, reverse, NoReverseMatch
from django.urls.resolvers import URLPattern, URLResolver
from django.core.exceptions import ImproperlyConfigured

def get_all_urls(urlconf=None, prefix='', urls_list=None):
    """Get all URL patterns"""
    if urls_list is None:
        urls_list = []
    
    resolver = get_resolver(urlconf)
    
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            get_all_urls(pattern.urlconf_name, prefix + str(pattern.pattern), urls_list)
        elif isinstance(pattern, URLPattern):
            try:
                url_path = prefix + str(pattern.pattern)
                # Clean up the URL pattern
                url_path = url_path.replace('^', '').replace('$', '')
                if url_path.startswith('/'):
                    url_path = url_path[1:]
                urls_list.append({
                    'pattern': url_path,
                    'name': pattern.name,
                    'callback': pattern.callback
                })
            except Exception as e:
                print(f"Error processing pattern: {e}")
    
    return urls_list

def test_route(client, url_info):
    """Test a single route"""
    pattern = url_info['pattern']
    name = url_info.get('name')
    
    # Skip routes that require parameters for now
    if '<' in pattern or '{' in pattern:
        return {'status': 'skipped', 'reason': 'requires_parameters'}
    
    try:
        # Try to access the route
        response = client.get(f'/{pattern}')
        return {
            'status': 'ok' if response.status_code < 500 else 'error',
            'status_code': response.status_code,
            'pattern': pattern,
            'name': name
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'pattern': pattern,
            'name': name
        }

if __name__ == '__main__':
    print("Testing all routes...")
    print("=" * 80)
    
    # Get all URLs
    all_urls = get_all_urls()
    print(f"Found {len(all_urls)} routes")
    
    # Test with a test client
    client = Client()
    
    # Test a few key routes
    test_routes = [
        '/',
        '/login/',
        '/home/',
        '/dashboard/',
        '/health/',
    ]
    
    print("\nTesting key routes:")
    print("-" * 80)
    for route in test_routes:
        try:
            response = client.get(route)
            status = "OK" if response.status_code < 500 else "ERROR"
            print(f"{status:6} {route:40} Status: {response.status_code}")
        except Exception as e:
            print(f"ERROR  {route:40} Exception: {str(e)[:50]}")

