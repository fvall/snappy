import os
import datetime
import shutil
import hashlib
import logging
import subprocess

from .rsync import NoRsyncError, RsyncError, is_rsync_installed, rsync
from .cmd import mv
from . import utils as ut


logger = logging.getLogger(__name__)


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
        logger.info(f"Backing up {src}")
        
        if not os.path.exists(src):
            logger.error(f"Folder {src} cannot be found")
            logger.error("Stopping snapshot")
            raise FileNotFoundError(f"Location {src} cannot be found. Stopping snapshot creation.")
        
        try:
            logger.info("Showing rsync logs:")
            logger.info("-------------------")
            output = rsync(src, dst, rsync_args + ["-av", "--delete"])
        except Exception as err:

            error_msg = _log_rsync_error(output)
            raise RsyncError(error_msg) from err

        if (output.returncode != 0):
            
            error_msg = _log_rsync_error(output)
            logger.error(f"Error code: {output.returncode}")
            raise RsyncError(error_msg)
        
        msg = f"Folder {src} backed up!"
        logger.info(msg)
        logger.info("-" * len(msg))


def snap_backup(sources: list, backup_folder: os.PathLike, max_backups = 3, rsync_args = None) -> None:
    
    # - If rsync is not installed, abort

    if not is_rsync_installed():
        logger.error("Command rsync cannot be found")
        logger.error("Aborting backup")
        raise NoRsyncError("Cannot find rsync in system's PATH")
    
    # - get existing backups and create new backup name

    backup_folder = ut.normalize_path(backup_folder)
    if not os.path.exists(backup_folder):
        logger.info(f"Destination folder {backup_folder} not found")
        logger.info(f"Creating folder {backup_folder}")
        os.makedirs(backup_folder)
    
    backups = get_backup_folders(backup_folder)
    now = datetime.datetime.now()
    new = now.strftime("%Y-%m-%d-%H_%M_%S")

    # - copy previous backup into tmp

    tmp = hashlib.md5(new.encode("utf8")).hexdigest()
    tmp = os.path.join(backup_folder, tmp)
    logger.info(f"Creating temporay folder {tmp}")
    os.makedirs(tmp)

    if rsync_args is None:
        rsync_args = []

    try:

        if backups:
            logger.info(f"Attempting to link snapshot files to {backups[-1]}")
            rsync_args.append(f"--link-dest={backups[-1]}")
        
        logger.info("Initiating snapshot creation")
        create_snapshot(sources, tmp, rsync_args)
    
    except Exception as err:

        # - if there is an error we rollback then raise
        
        logger.error("Starting rollback")
        logger.error(f"Removing temporary folder {tmp}")
        shutil.rmtree(tmp)

        raise RuntimeError from err

    # - if it succeeds, we rename tmp file and clean old backups

    new = os.path.join(backup_folder, new)
    logger.info(f"Moving temporary folder {tmp} to {new}")
    mv(tmp, new)

    logger.info("Cleaning old backups")
    clean_backups(backup_folder, max_backups)


def clean_backups(path: os.PathLike, n: int) -> None:

    if n <= 0:
        logger.info("No old backups to remove")
        return None

    backups = get_backup_folders(path)
    backups.reverse()
    if len(backups) > n:
        for bk in backups[n:]:
            logger.info(f"Removing backup {os.path.basename(bk)}")
            shutil.rmtree(bk)

# ---------------------
#  Internal functions
# ---------------------


def _log_rsync_error(cmd_output: subprocess.Popen) -> str:

    logger.error("There was an error when running the backup")
    logger.error("Error message")

    error_msg = cmd_output.stderr.readlines()
    msg = error_msg.split("\n")
    for m in msg:
        if (m != "") and (m != "\n") and (m != "\n\n"):
            logger.error(m)

    return error_msg
