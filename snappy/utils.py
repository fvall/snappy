import os


def substitute_tilde(path):
    if path[0] == "~":
        path = os.environ["HOME"] + path[1:]
    
    return path


def normalize_path(path):
        
    need_sep = (path[-1] == os.path.sep)
    path = substitute_tilde(path)
    path = os.path.abspath(path)
    if need_sep:
        path += os.path.sep
    return path
