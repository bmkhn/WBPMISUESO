"""
Script to verify all views exist and can be imported
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WBPMISUESO.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def test_views(urlconf=None, prefix=''):
    """Test all views can be imported"""
    resolver = get_resolver(urlconf)
    errors = []
    
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            try:
                sub_errors = test_views(pattern.urlconf_name, prefix + str(pattern.pattern))
                errors.extend(sub_errors)
            except Exception as e:
                errors.append({
                    'url': prefix + str(pattern.pattern),
                    'error': f'Error loading URL config: {str(e)}',
                    'type': 'URLConfigError'
                })
        elif isinstance(pattern, URLPattern):
            try:
                # Try to access the view
                view = pattern.callback
                # Try to get the view function/class
                if hasattr(view, 'view_class'):
                    view_class = view.view_class
                    # Try to instantiate if it's a class-based view
                    if hasattr(view_class, 'as_view'):
                        pass  # It's a class-based view, that's fine
                else:
                    # It's a function-based view, check if it's callable
                    if not callable(view):
                        errors.append({
                            'url': prefix + str(pattern.pattern),
                            'error': 'View is not callable',
                            'type': 'ViewNotCallable'
                        })
            except Exception as e:
                errors.append({
                    'url': prefix + str(pattern.pattern),
                    'error': f'Error accessing view: {str(e)}',
                    'type': 'ViewAccessError'
                })
    
    return errors

if __name__ == '__main__':
    print("Testing all views...")
    print("=" * 80)
    
    errors = test_views()
    
    if errors:
        print(f"\nFound {len(errors)} error(s):")
        for error in errors:
            print(f"\nURL: {error.get('url', 'Unknown')}")
            print(f"Type: {error.get('type', 'Unknown')}")
            print(f"Error: {error.get('error', 'Unknown error')}")
        sys.exit(1)
    else:
        print("\n[OK] All views are accessible!")

