"""
Script to check all URL routes for errors
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WBPMISUESO.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import get_resolver
from django.core.exceptions import ViewDoesNotExist
from django.urls.resolvers import URLPattern, URLResolver

def check_urls(urlconf=None, prefix=''):
    """Recursively check all URLs for errors"""
    resolver = get_resolver(urlconf)
    errors = []
    
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            # Recursive check for included URL configs
            try:
                sub_errors = check_urls(pattern.urlconf_name, prefix + str(pattern.pattern))
                errors.extend(sub_errors)
            except Exception as e:
                errors.append({
                    'url': prefix + str(pattern.pattern),
                    'error': f'Error loading URL config: {str(e)}',
                    'type': 'URLConfigError'
                })
        elif isinstance(pattern, URLPattern):
            # Check if view exists
            try:
                view = pattern.callback
                if hasattr(view, 'view_class'):
                    # Class-based view
                    view_class = view.view_class
                    errors.append({
                        'url': prefix + str(pattern.pattern),
                        'view': f'{view_class.__module__}.{view_class.__name__}',
                        'status': 'OK'
                    })
                else:
                    # Function-based view
                    errors.append({
                        'url': prefix + str(pattern.pattern),
                        'view': f'{view.__module__}.{view.__name__}',
                        'status': 'OK'
                    })
            except ViewDoesNotExist as e:
                errors.append({
                    'url': prefix + str(pattern.pattern),
                    'error': f'View does not exist: {str(e)}',
                    'type': 'ViewNotFound'
                })
            except Exception as e:
                errors.append({
                    'url': prefix + str(pattern.pattern),
                    'error': f'Error: {str(e)}',
                    'type': 'UnknownError'
                })
    
    return errors

if __name__ == '__main__':
    print("Checking all URL routes...")
    print("=" * 80)
    
    errors = check_urls()
    
    # Separate errors from successful routes
    successful = [e for e in errors if e.get('status') == 'OK']
    failed = [e for e in errors if e.get('status') != 'OK']
    
    print(f"\nTotal routes checked: {len(errors)}")
    print(f"Successful: {len(successful)}")
    print(f"Errors: {len(failed)}")
    
    if failed:
        print("\n" + "=" * 80)
        print("ERRORS FOUND:")
        print("=" * 80)
        for error in failed:
            print(f"\nURL: {error.get('url', 'Unknown')}")
            print(f"Type: {error.get('type', 'Unknown')}")
            print(f"Error: {error.get('error', 'Unknown error')}")
    
    if not failed:
        print("\n[OK] All URL routes are valid!")
    else:
        print(f"\n[ERROR] Found {len(failed)} error(s)")
        sys.exit(1)

