import os
import subprocess
from .utils import substitute_tilde


class NoRsync(Exception):
    pass


def has_rsync_installed() -> bool:
    cmd = ["rsync", "--version"]
    out = subprocess.run(cmd, stdout = subprocess.DEVNULL, capture_output = False)
    return (out.returncode == 0)


def rsync(src, dst, options = None):

    if options is None:
        options = []
    
    default = "-av"
    opt = [default] + options

    # - substitute "~" for home directory

    src = substitute_tilde(src)
    dst = substitute_tilde(dst)
    
    # - paths should be absolute
    
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)

    cmd = ["rsync"] + opt + [src, dst]
    out = subprocess.run(cmd, capture_output = True)
    return out
