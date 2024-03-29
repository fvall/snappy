import os
import re
import datetime
import shutil
import hashlib
import logging
import subprocess

from .rsync import (
    NoRsyncError,
    RsyncError,
    is_rsync_installed,
    rsync,
    exclude_from_rsync,
)

from .cmd import mv, find_non_readable
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
        ftype = "folder" if os.path.isdir(src) else "file"
        logger.info(f"Backing up {ftype} {src}")

        if not os.path.exists(src):
            logger.error(f"{ftype.capitalize()} {src} cannot be found")
            logger.error("Stopping snapshot")
            raise FileNotFoundError(f"Location {src} cannot be found. Stopping snapshot creation.")
        
        try:
            non_readable = _list_non_readable_files(src)
            for idx, nr in enumerate(non_readable):
                nr = re.sub(f"^{src}", "", nr)
                if not nr.startswith(os.path.sep):
                    nr = os.path.sep + nr

                non_readable[idx] = nr
        except Exception as err:
            logger.error(f"There was an error when trying to find non-readable files in {src}")
            _log_error(str(err))
            raise RsyncError(str(err)) from err

        try:
            logger.info("Showing rsync logs:")
            logger.info("-------------------")
            rsync_excl = exclude_from_rsync(non_readable)
            for rse in non_readable:
                logger.warning(f"This file will be excluded from the backup: {rse}")

            output = rsync(src, dst, rsync_args + ["-av", "--delete"] + rsync_excl)
        except Exception as err:

            error_msg = _log_rsync_error(output)
            raise RsyncError(error_msg) from err

        if (output.returncode != 0):
            
            error_msg = _log_rsync_error(output)
            logger.error(f"Error code: {output.returncode}")
            raise RsyncError(error_msg)
        
        msg = f"{ftype.capitalize()} {src} backed up!"
        logger.info(msg)
        logger.info("-" * len(msg))


def snap_backup(sources: list, backup_folder: os.PathLike, max_backups = 3, rsync_args = None) -> str:
    
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
        
        logger.info("Creating backup snapshot...")
        create_snapshot(sources, tmp, rsync_args)
    
    except Exception as err:

        # - if there is an error we rollback then raise
        
        logger.error("Starting rollback")
        logger.error(f"Removing temporary folder {tmp}")
        shutil.rmtree(tmp)

        raise RuntimeError from err

    # - if it succeeds, we rename tmp file and clean old backups

    if "--dry-run" in rsync_args:
        shutil.rmtree(tmp)
        return new

    new = os.path.join(backup_folder, new)
    logger.info(f"Moving temporary folder {tmp} to {new}")
    mv(tmp, new)

    logger.info("Cleaning old backups")
    clean_backups(backup_folder, max_backups)
    return os.path.basename(new)


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
    else:
        logger.info("No old backups to remove")


# ---------------------
#  Internal functions
# ---------------------


def _log_error(error_msg):
    msg = error_msg.split("\n")
    for m in msg:
        if (m != "") and (m != "\n") and (m != "\n\n"):
            logger.error(m)


def _log_rsync_error(cmd_output: subprocess.Popen) -> str:

    logger.error("There was an error when running the backup")
    logger.error("Error message")

    stdout = cmd_output.stdout.readlines()
    stderr = cmd_output.stderr.readlines()
    error_msg = stderr if stderr else stdout
    for msg in error_msg:
        _log_error(msg)

    return error_msg


def _list_non_readable_files(src):

    # - rsync cannot copy non-readable files so we try to identify
    # - those and if so we automatically exclude them from the
    # - rsync sources

    out = find_non_readable(src)
    if out.returncode != 0:
        # - there was an error and hence we do not do anything
        _log_error(out.stderr)
        return []

    if out.stdout is None:
        return []

    files = out.stdout.decode("utf-8").split("\n")
    files = (f.strip() for f in files)
    files = (f for f in files if f != "")
    return list(files)
