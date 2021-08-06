import os
import datetime
import shutil
import hashlib

from .rsync import NoRsyncError, RsyncError, is_rsync_installed, rsync
from .cmd import mv
from . import utils as ut


def get_backup_folders(path: os.PathLike) -> list:

    path = os.path.abspath(path)
    folders = os.listdir(path)
    folders = (os.path.join(path, f) for f in folders)
    folders = [f for f in folders if os.path.isdir(f)]
    folders.sort()
    return folders


def create_snapshot(sources: list, destination: os.PathLike, rsync_args = None) -> None:

    # ------------------------------------------------
    #  Create a backup of each source to destination
    #  Destination will contain each source
    # ------------------------------------------------

    if rsync_args is None:
        rsync_args = []

    dst = ut.normalize_path(destination)
    if dst[-1] != os.path.sep:
        dst += os.path.sep
    
    for src in sources:

        src = ut.normalize_path(src)
        if not os.path.exists(src):
            raise RuntimeError(f"Location {src} cannot be found. Stopping snapshot creation.")
        
        try:
            output = rsync(src, dst, rsync_args + ["-av", "--delete"])
        except Exception as err:
            raise RsyncError(output.stderr.decode("utf8")) from err

        try:
            output.check_returncode()
        except Exception as err:
            raise RsyncError(output.stderr.decode("utf8")) from err


def snap_backup(sources: list, backup_folder: os.PathLike, max_backups = 3, rsync_args = None) -> None:
    
    # - If rsync is not installed, abort

    if not is_rsync_installed():
        raise NoRsyncError("Cannot find rsync in system's PATH")
    
    # - get existing backups and create new backup name

    backup_folder = os.path.abspath(backup_folder)
    backups = get_backup_folders(backup_folder)
    now = datetime.datetime.now()
    new = now.strftime("%Y-%m-%d-%H_%M_%S")

    # - copy previous backup into tmp

    tmp = hashlib.md5(new.encode("utf8")).hexdigest()
    tmp = os.path.join(backup_folder, tmp)
    os.makedirs(tmp)

    if rsync_args is None:
        rsync_args = []

    try:

        if backups:
            rsync_args.append(f"--link-dest={backups[-1]}")
        
        create_snapshot(sources, tmp, rsync_args)
    
    except Exception as err:

        # - if there is an error we rollback then raise
        
        shutil.rmtree(tmp)
        raise RuntimeError from err

    # - if it suceeds, we rename tmp file and clean old backups

    new = os.path.join(backup_folder, new)
    mv(tmp, new)
    clean_backups(backup_folder, max_backups)


def clean_backups(path: os.PathLike, n: int) -> None:

    if n <= 0:
        return None

    backups = get_backup_folders(path)
    backups.reverse()
    if len(backups) > n:
        for bk in backups[n:]:
            shutil.rmtree(bk)
