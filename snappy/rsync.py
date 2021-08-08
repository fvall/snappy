import logging
import datetime
import subprocess
from subprocess import PIPE
from .cmd import _fs_cmd_args

logger = logging.getLogger(__name__)


class NoRsyncError(FileNotFoundError):
    pass


class RsyncError(RuntimeError):
    pass


def is_rsync_installed() -> bool:
    cmd = ["which", "rsync"]
    out = subprocess.run(cmd, capture_output = True)
    return (out.returncode == 0)


def rsync(src, dst, options = None):

    args = _fs_cmd_args(src, dst, options)
    default = "-av"

    opt = [default] + args.options
    cmd = ["rsync"] + opt + [args.src, args.dst]
    logger.debug(f"Running command {cmd}")

    out = subprocess.Popen(cmd, stdout = PIPE, stderr = PIPE, encoding = "utf8")
    now = datetime.datetime.now()
    while True:

        elapsed = datetime.datetime.now() - now
        s = out.stdout.readline()
        
        if s.endswith("\n"):
            s = s[:-1]

        if s != "":
            logger.info(s)
        
        if (out.poll() is not None) and (elapsed.seconds > 1) and (s == ""):
            break

    return out
