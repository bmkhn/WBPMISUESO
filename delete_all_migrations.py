import os
import glob
import shutil

# Only delete migrations in project app folders, not in venv or site-packages
EXCLUDE_DIRS = {'venv', 'env', '.venv', 'Lib', 'Scripts', 'bin', 'Include', 'site-packages', '__pycache__'}


def is_project_dir(path):
    # Use absolute path for robust matching
    abs_path = os.path.abspath(path)
    for ex in EXCLUDE_DIRS:
        if ex in abs_path.split(os.sep):
            return False
    return True

# Delete migration .py and .pyc files (except __init__.py) in project apps only
for root, dirs, files in os.walk('.'):
    if not is_project_dir(root):
        continue
    if 'migrations' in dirs:
        mig_dir = os.path.join(root, 'migrations')
        for mig_file in glob.glob(os.path.join(mig_dir, '*.py')):
            if not mig_file.endswith('__init__.py'):
                os.remove(mig_file)
        for mig_file in glob.glob(os.path.join(mig_dir, '*.pyc')):
            os.remove(mig_file)

# Recursively delete all __pycache__ folders in project only
for root, dirs, files in os.walk('.'):
    if not is_project_dir(root):
        continue
    for d in dirs:
        if d == '__pycache__':
            cache_dir = os.path.join(root, d)
            shutil.rmtree(cache_dir)
print("All migration .py and .pyc files deleted (except __init__.py) in project apps, and all __pycache__ folders removed from project.")