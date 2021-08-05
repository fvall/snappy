import os
import subprocess
from .cmd import _fs_cmd_args


class NoRsyncError(FileNotFoundError):
    pass


def is_rsync_installed() -> bool:
    cmd = ["rsync", "--version"]
    out = subprocess.run(cmd, stdout = subprocess.DEVNULL, capture_output = False)
    return (out.returncode == 0)


def rsync(src, dst, options = None):

    args = _fs_cmd_args(src, dst, options)
    default = "-av"

    opt = [default] + args.options
    cmd = ["rsync"] + opt + [args.src, args.dst]
    out = subprocess.run(cmd, capture_output = True)

    return out
