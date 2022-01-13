import os
import io
import logging
import datetime
import argparse
import subprocess
from .rsync import RsyncError
from .cmd import mv
from . import config as cfg
from . import snappy as snp
from . import utils as ut

logger = logging.getLogger("snappy")


# ----------------
#  CLI functions
# ----------------

def create_config() -> None:

    _configure_logger(verbose = True)
    try:
        cfg.create_config()
    except Exception as err:
        logger.error("Cannot create configuration file")
        logger.error("Error message:")

        msg = str(err)
        for m in msg.split("\n"):
            if m != "":
                logger.error(m)
        
        raise RuntimeError(f"Cannot create default config file in {cfg.config_loc()}") from err

    print("")


def show_config() -> None:
    
    sio = io.StringIO("\n")
    sio.seek(1)

    try:
        config = cfg.read_config()
    except Exception as err:
        sio.close()
        raise RuntimeError(f"Cannot read config file from default location {cfg.config_loc()}") from err

    title = "Configuration file"
    sio.write(title)
    sio.write("\n")
    sio.write("-" * len(title))
    sio.write("\n")
    
    config.write(sio, False)
    print(sio.getvalue())
    
    sio.truncate(0)
    sio.close()


def config_path() -> None:
    print(f"Path: {ut.normalize_path(cfg.config_loc())}")


def run_backup(verbose = True, dry_run = True) -> None:
    
    _configure_logger(verbose)

    config = cfg.read_config()
    if not cfg.is_valid_config(config):
        msg = "Config file is invalid. Please fix the file and try again."
        logger.error(msg)
        raise cfg.InvalidConfigError(msg)
    
    # -------------------------
    #  Source and destination
    # -------------------------

    dst = config["Destination"]["folder"]
    src = config["Sources"].keys()
    src = filter(lambda x: x is not None, src)
    src = filter(lambda x: x != "", src)
    src = filter(lambda x: not is_comment(x), src)
    src = [s.strip() for s in src]
    dst = dst.strip()

    # ------------------------
    #  Number of max backups
    # ------------------------

    size = [k for k in config["backup.quantity"].keys() if not is_comment(k)]
    size = size[0] if size else 0
    size = int(size.strip())

    # ------------------------------
    #  Process extra args to rsync
    # ------------------------------

    args = []

    # - rsync exclude patterns

    rsync_exclude = _process_rsync_patterns(config, "rsync.exclude")
    for idx, e in enumerate(rsync_exclude):
        rsync_exclude[idx] = f"--exclude={ut.substitute_tilde(e)}"

    args += rsync_exclude

    # - rsync include patterns

    rsync_include = _process_rsync_patterns(config, "rsync.include")
    for idx, e in enumerate(rsync_include):
        rsync_include[idx] = f"--include={ut.substitute_tilde(e)}"

    args += rsync_include

    # - Dry run

    if dry_run:
        args.append("--dry-run")

    # ---------------
    #  Start backup
    # ---------------

    now = datetime.datetime.now()
    msg = f"Starting backup on {now.strftime('%d-%b-%Y')} at {now.strftime('%H:%M:%S')}"
    logger.info(msg)
    logger.info("=" * len(msg))

    try:
        backup_folder = snp.snap_backup(src, dst, size, args)
    except Exception as err:
        msg = "There was an error when creating the backup"
        logger.error(msg)
        raise RsyncError(msg) from err

    _compress_log(logger, backup_folder)

# --------------
#  CLI program
# --------------


def cli_config(show: bool = True, path: bool = False, create: bool = False, **kws) -> int:

    if show:
        show_config()
    
    if path:
        config_path()
    
    if create:
        create_config()

    return 0


def cli_snap(quiet: bool = False, dry_run: bool = True, **kws) -> int:
    
    verbose = True if dry_run else (not quiet)
    try:
        run_backup(verbose = verbose, dry_run = dry_run)
    except cfg.ConfigReadError:
        return 1
    except cfg.ConfigNotFoundError:
        return 1
    except cfg.InvalidConfigError:
        return 1
    except snp.RsyncError:
        return 2
    
    return 0


def cli():
    
    # -----------------------
    #  Parser and subparser
    # -----------------------

    description = '''Snappy - backup snapshots with rsync
    ====================================

    Create backup snapshots based on config file specification. There are two commands:
    * snap --- create snapshots
    * config --- config utilities

    Each command has its dedicated section. You can use snappy [COMMAND] -h to show the description of each command.
    Logs are saved in $HOME/.logs/snappy if the process can write to that location.
    '''

    description = description.replace("\n    ", "\n")
    description = description.replace("* ", "    * ")

    prog = "snappy"
    parser = argparse.ArgumentParser(
        description = description,
        prog = prog,
        formatter_class = argparse.RawTextHelpFormatter
    )

    def helper(**kws):
        parser.print_help()
        return 0
    
    parser.set_defaults(func = helper)
    subparser = parser.add_subparsers(prog = "snappy", title = "commands")

    # ---------------
    #  Snap command
    # ---------------

    description = "Create backup snapshot\n======================"
    epilog = """This command creates a backup snapshot based on the configuration file
    * You can disable the backup steps by using the option --quiet. This still saves the logs to a file.
    * If you would like to test the tool you can use the option --dry-run. This will print the backup steps, but no backup will be created.
    """

    snap = subparser.add_parser(
        "snap",
        description = description,
        epilog = epilog,
        formatter_class = argparse.RawTextHelpFormatter
    )
    snap.set_defaults(func = cli_snap)

    # -- quiet argument

    default = False
    action = "store_true"
    help = "don't show steps while backing up"
    snap.add_argument("-q", "--quiet", default = default, action = action, help = help)

    # -- dry-run argument

    default = False
    action = "store_true"
    help = "perform trial run without making any changes (disables quiet)"
    snap.add_argument("--dry-run", default = default, action = action, help = help)

    # ----------------
    #  Config command
    # ----------------

    description = "Snappy backup configuration\n==========================="
    usage = "%(prog)s [options]"
    epilog = """Use this command to manage the configuration file
    * You can create a default configuration file if one does not exist. This does not overwrite an existing configuration file.
    * You can also show the configuration without opening the file, which is handy if you are already in terminal.
    * If you forgot where the file is saved, you can print the file path as well.
    """

    config = subparser.add_parser(
        "config",
        description = description,
        usage = usage,
        epilog = epilog,
        formatter_class = argparse.RawTextHelpFormatter
    )
    config.set_defaults(func = cli_config)
    
    # - show argument

    default = False
    action = "store_true"
    help = "print configuration"
    
    config.add_argument("-s", "--show", default = default, action = action, help = help)
    
    # - path argument

    default = False
    action = "store_true"
    help = "show config file location"
    
    config.add_argument("-p", "--path", default = default, action = action, help = help)
    
    # - path argument

    default = False
    action = "store_true"
    help = "create default configuration file"
    
    config.add_argument("-c", "--create", default = default, action = action, help = help)

    # -------------
    #  Run parser
    # -------------

    args = parser.parse_args()
    return args.func(**vars(args))

# ---------------------
#  Internal functions
# ---------------------


def _configure_logger(verbose = True) -> None:
    
    logger.setLevel(logging.INFO)

    # -----------------
    #  Log to console
    # -----------------

    chl = _stream_handler()
    if verbose:
        chl.setLevel(logging.INFO)
    else:
        chl.setLevel(logging.WARNING)

    # --------------
    #  Log to file
    # --------------

    fhl = _file_handler()

    # -----------------------------------------
    #  Check if we need to update the handlers
    # -----------------------------------------

    add_handler = {
        "Console" : chl,
        "File" : fhl
    }

    if logger.hasHandlers():
        
        for idx, lhl in enumerate(logger.handlers):
            if lhl.get_name() in add_handler:
                logger.handlers[idx] = add_handler[lhl.get_name()]
                add_handler.pop(lhl.get_name())
    
    if add_handler:
        for hl in add_handler.values():
            logger.addHandler(hl)


def _file_handler() -> logging.FileHandler:

    loc = os.path.join(os.environ["HOME"], ".logs", "snappy")
    today = datetime.date.today()
    file = today.strftime("%Y-%m-%d") + ".log"

    if not os.path.exists(loc):
        try:
            os.makedirs(loc)
        except Exception as err:
            msg = f"Cannot create log directory {loc}"
            raise RuntimeError(msg) from err
    
    file = os.path.join(loc, file)
    hl = logging.FileHandler(file, encoding = "utf8")
    hl.set_name("File")
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    hl.setFormatter(fmt)

    return hl


def _stream_handler() -> logging.StreamHandler:

    hl = logging.StreamHandler()
    hl.set_name("Console")
    fmt = logging.Formatter("%(message)s")
    hl.setFormatter(fmt)

    return hl


def _compress_log(lg, name) -> None:

    for hl in lg.handlers:
        if hl.get_name() == "File":
            file = hl.baseFilename
            if not os.path.exists(file):
                return None

            name = os.path.join(os.path.dirname(file), name)
            name += ".log"
            lg.info("Moving file '{}' to '{}'".format(file, name))
            mv(file, name)
            
            lg.info("Compressing file '{}'".format(name))
            cmd = ["gzip", "--best", '{}'.format(name)]
            try:
                lg.info("Running command '{}'".format(" ".join(cmd)))
                out = subprocess.run(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            except Exception:
                lg.error("Could not compress log file '{}'".format(file))
                mv(name, file)
                return

            if out.returncode != 0:
                lg.error("Could not compress log file '{}'".format(file))
                mv(name, file)
            
            return None


def _process_rsync_patterns(config, section):
    
    patt = list(config[section].keys())
    patt_list = []
    for e in patt:
        if e != "" and (not is_comment(e)):
            patt_list.append(e.strip())
    
    return patt


def is_comment(s):

    # - Something is a comment if it starts with #

    return s[0] == "#"
