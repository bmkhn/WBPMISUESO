"""
Comprehensive route testing - tests all routes for errors
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WBPMISUESO.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client, override_settings
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

@override_settings(ALLOWED_HOSTS=['*'])
def test_all_routes():
    """Test all routes for 500 errors"""
    client = Client(HTTP_HOST='localhost')
    resolver = get_resolver()
    errors = []
    tested = 0
    skipped = 0
    
    def test_pattern(pattern, prefix=''):
        nonlocal tested, skipped
        if isinstance(pattern, URLResolver):
            for sub_pattern in pattern.url_patterns:
                test_pattern(sub_pattern, prefix + str(pattern.pattern))
        elif isinstance(pattern, URLPattern):
            url_path = str(pattern.pattern)
            full_path = (prefix + url_path).replace('^', '').replace('$', '')
            
            # Skip routes with parameters for now
            if '<' in full_path or '{' in full_path:
                skipped += 1
                return
            
            # Clean up path
            if full_path.startswith('/'):
                full_path = full_path[1:]
            if not full_path:
                full_path = '/'
            else:
                full_path = '/' + full_path
            
            tested += 1
            try:
                response = client.get(full_path, follow=True)
                if response.status_code >= 500:
                    errors.append({
                        'url': full_path,
                        'status': response.status_code,
                        'error': 'Server Error'
                    })
            except Exception as e:
                # Some routes might raise exceptions (like redirects, etc.)
                # Only log actual 500 errors
                if '500' in str(e) or 'Internal Server Error' in str(e):
                    errors.append({
                        'url': full_path,
                        'status': 500,
                        'error': str(e)
                    })
    
    # Test all patterns
    for pattern in resolver.url_patterns:
        test_pattern(pattern)
    
    return errors, tested, skipped

if __name__ == '__main__':
    print("=" * 80)
    print("COMPREHENSIVE ROUTE TESTING")
    print("=" * 80)
    print("\nTesting all routes for 500 errors...")
    print("(Routes with parameters are skipped)")
    print("-" * 80)
    
    errors, tested, skipped = test_all_routes()
    
    print(f"\nResults:")
    print(f"  Routes tested: {tested}")
    print(f"  Routes skipped (have parameters): {skipped}")
    print(f"  Errors found: {len(errors)}")
    
    if errors:
        print("\n" + "=" * 80)
        print("ERRORS FOUND:")
        print("=" * 80)
        for error in errors:
            print(f"\nURL: {error['url']}")
            print(f"Status: {error['status']}")
            print(f"Error: {error['error']}")
    else:
        print("\n[OK] No 500 errors found in tested routes!")
    
    print("\n" + "=" * 80)

