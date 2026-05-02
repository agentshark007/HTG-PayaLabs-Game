import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_absolute_path(path):
    return str(os.path.join(BASE_DIR, path))
