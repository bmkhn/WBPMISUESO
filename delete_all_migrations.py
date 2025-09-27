import os
import glob
import shutil

# Delete migration .py and .pyc files (except __init__.py)
for root, dirs, files in os.walk('.'):
    if 'migrations' in dirs:
        mig_dir = os.path.join(root, 'migrations')
        for mig_file in glob.glob(os.path.join(mig_dir, '*.py')):
            if not mig_file.endswith('__init__.py'):
                os.remove(mig_file)
        for mig_file in glob.glob(os.path.join(mig_dir, '*.pyc')):
            os.remove(mig_file)

# Recursively delete all __pycache__ folders project-wide
for root, dirs, files in os.walk('.'):
    for d in dirs:
        if d == '__pycache__':
            cache_dir = os.path.join(root, d)
            shutil.rmtree(cache_dir)
print("All migration .py and .pyc files deleted (except __init__.py), and all __pycache__ folders removed.")