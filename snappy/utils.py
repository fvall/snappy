import os


def substitute_tilde(path):
    if path[0] == "~":
        path = os.environ["HOME"] + path[1:]
    
    return path
