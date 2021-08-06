import subprocess
import shutil
from .utils import normalize_path


class FsCmdArgs:

    def __init__(self, src, dst, options = None) -> None:
        
        self.src = src
        self.dst = dst
        self.options = options


def _fs_cmd_args(src, dst, options = None):

    if options is None:
        options = []

    src = normalize_path(src)
    dst = normalize_path(dst)

    return FsCmdArgs(src, dst, options)


def cp(src, dst, options = None):
    
    args = _fs_cmd_args(src, dst, options)
    cmd = ["cp"] + args.options + [args.src, args.dst]
    out = subprocess.run(cmd, capture_output = True)

    return out


def mv(src, dst):
    args = _fs_cmd_args(src, dst)
    return shutil.move(args.src, args.dst)
