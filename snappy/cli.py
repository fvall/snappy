import io
import logging
import datetime
import argparse
from time import strftime
from . import config as cfg
from . import snappy as snp


logger = logging.getLogger("snappy")


def create_config() -> None:
    try:
        cfg.create_config()
    except Exception as err:
        raise RuntimeError(f"Cannot create default config file in {cfg.config_loc()}") from err


def show_config() -> None:
    
    sio = io.StringIO("\n")
    sio.seek(1)

    try:
        config = cfg.read_config()
    except Exception as err:
        sio.close()
        raise RuntimeError(f"Cannot read config file from default location {cfg.config_loc()}") from err

    config.write(sio, False)
    print(sio.getvalue())
    
    sio.truncate(0)
    sio.close()


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
    
    now = datetime.datetime.now()
    msg = f"Starting backup on {now.strftime('%d-%b-%Y')} at {now.strftime('%H:%M:%S')}"
    logger.info(msg)
    logger.info("=" * len(msg))

    args = []
    if dry_run:
        args.append("--dry-run")

    snp.snap_backup(src, dst, size, args)
