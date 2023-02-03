import os


def substitute_tilde(path):
    return os.path.expanduser(path)


def normalize_path(path):
        
    need_sep = (path[-1] == os.path.sep)
    path = substitute_tilde(path)
    path = os.path.abspath(path)
    if need_sep:
        path += os.path.sep
    return path
