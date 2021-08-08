import os
import logging
import configparser

loc = os.path.abspath(__file__)
default_config_loc = os.path.join(os.path.dirname(loc), "assets", "snappy.ini")
logger = logging.getLogger(__name__)


class ConfigNotFoundError(FileNotFoundError):
    pass


class ConfigReadError(RuntimeError):
    pass


class InvalidConfigError(ValueError):
    pass


def config_loc() -> str:
    return os.path.join(os.environ["HOME"], ".config", "snappy")


def create_config() -> None:

    loc = config_loc()
    logger.info(f"Creating config file in {loc}")
    os.makedirs(loc, exist_ok = True)

    file = os.path.join(loc, "snappy.ini")
    if os.path.exists(file):
        logger.info("Configuration file already exists")
        logger.info("Skipping file creation")
        return None
    
    with open(file, "w") as fw:
        with open(default_config_loc, "r") as fr:
            fw.write(fr.read())
    
    logger.info("Configuration file created")
    return None


def read_config() -> configparser.ConfigParser:

    loc = config_loc()
    file = os.path.join(loc, "snappy.ini")
    if not os.path.exists(file):
        logger.error(f"Cannot find snappy config folder {loc}")
        logger.error("Please create one with `snappy config --create`")
        raise ConfigNotFoundError(f"Cannot find snappy config folder {loc}")
    
    cfg = configparser.ConfigParser(
        interpolation = configparser.ExtendedInterpolation(),
        allow_no_value = True
    )

    cfg.optionxform = lambda s: s
    
    try:
        cfg.read(file)
    except Exception as err:
        raise ConfigReadError("Cannot read config file") from err

    return cfg


def is_valid_config(cfg) -> bool:

    # --> need to have a key folder under Destination

    try:
        cfg["Destination"]["folder"]
    except KeyError:
        return False
    
    # --> need to have at least one source

    try:
        sources = list(cfg["Sources"].keys())
    except KeyError:
        return False

    if not sources:
        return False

    # --> backup quantity must be empty or a number

    try:
        qty = list(cfg["backup.quantity"].keys())
    except KeyError:
        return False

    if qty:
        try:
            qty = int(qty[0])
        except ValueError:
            return False

    # --> must have rsync.exclude section

    try:
        list(cfg["rsync.exclude"].keys())
    except KeyError:
        return False
    
    # --> must have rsync.include section

    try:
        list(cfg["rsync.include"].keys())
    except KeyError:
        return False

    return True
