import io
import logging
import datetime
import argparse
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
    
    config = cfg.read_config()
    if not cfg.is_valid_config(config):
        raise ValueError("Config file is invalid. Please fix the file and try again.")
    
    dst = config["Destination"]["folder"]
    src = config["Sources"].keys()
    src = filter(lambda x: x is not None, src)
    src = filter(lambda x: x != "", src)
    src = list(src)

    size = list(config["backup.quantity"].keys())
    size = size[0] if size else 0
    size = int(size)
    
    _configure_logger(verbose)

    now = datetime.datetime.now()
    msg = f"Starting backup on {now.strftime('%d-%b-%Y')} at {now.strftime('%H:%M:%S')}"
    logger.info(msg)
    logger.info("=" * len(msg))

    args = []
    if dry_run:
        args.append("--dry-run")

    snp.snap_backup(src, dst, size, args)

# --------------
#  CLI program
# --------------


def cli_config(show = True, path = False, create = False, **kws):

    if show:
        show_config()
    
    if path:
        config_path()
    
    if create:
        create_config()


def cli_snap(verbose = True, dry_run = True, **kws):
    verbose = True if dry_run else verbose
    run_backup(verbose = verbose, dry_run = dry_run)


def cli():
    
    parser = argparse.ArgumentParser(description = 'Snappy - create backup snapshots with rsync', prog = "snappy")
    subparser = parser.add_subparsers(prog = "snappy")

    # ---------------
    #  Snap command
    # ---------------

    description = "Create backup snapshot"
    snap = subparser.add_parser("snap", description = description)
    snap.set_defaults(func = cli_snap)

    # -- dry-run argument

    default = True
    action = "store_true"
    help = "perform trial run without making any changes (sets verbose to true)"
    snap.add_argument("--dry-run", default = default, action = action, help = help)

    # -- verbose argument

    default = False
    action = "store_true"
    help = "show information while backing up"
    snap.add_argument("-v", "--verbose", default = default, action = action, help = help)

    # ----------------
    #  Config command
    # ----------------

    config = subparser.add_parser("config", description = "Snappy backup configuration", usage = "%(prog)s [options]", epilog = "AAAAA BBBBB CCCC\nDDDDD EEEEE")
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
    print(args)
    args.func(**vars(args))

    return args

# ---------------------
#  Internal functions
# ---------------------


def _configure_logger(verbose = True) -> None:
    
    logger.setLevel(logging.INFO)
    hl = logging.StreamHandler()
    hl.set_name("Console")
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    hl.setFormatter(fmt)
    if verbose:
        hl.setLevel(logging.INFO)
    else:
        hl.setLevel(logging.WARNING)

    add_handler = True
    if logger.hasHandlers():
        
        for idx, lhl in enumerate(logger.handlers):
            if lhl.get_name() == "Console":
                logger.handlers[idx] = hl
                add_handler = False
                break
    
    if add_handler:
        logger.addHandler(hl)
