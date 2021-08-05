import os
import subprocess
import shutil
from .utils import substitute_tilde


class FsCmdArgs:

    def __init__(self, src, dst, options = None) -> None:
        
        self.src = src
        self.dst = dst
        self.options = options


def _fs_cmd_args(src, dst, options = None):

    if options is None:
        options = []

    # - substitute "~" for home directory

    src = substitute_tilde(src)
    dst = substitute_tilde(dst)
    
    # - paths should be absolute
    
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)

    return FsCmdArgs(src, dst, options)


def cp(src, dst, options = None):
    
    args = _fs_cmd_args(src, dst, options)
    cmd = ["cp"] + args.options + [args.src, args.dst]
    out = subprocess.run(cmd, capture_output = True)

    return out


def mv(src, dst):
    args = _fs_cmd_args(src, dst)
    return shutil.move(args.src, args.dst)
