import os
import configparser

loc = os.path.abspath(__file__)
default_config_loc = os.path.join(os.path.dirname(loc), "assets", "snappy.ini")


def config_loc() -> str:
    return os.path.join(os.environ["HOME"], ".config", "snappy")


def create_config() -> None:

    loc = config_loc()
    os.makedirs(loc, exist_ok = True)

    file = os.path.join(loc, "snappy.ini")
    if os.path.exists(file):
        return None
    
    with open(file, "w") as fw:
        with open(default_config_loc, "r") as fr:
            fw.write(fr.read())


def read_config() -> configparser.ConfigParser:

    loc = config_loc()
    file = os.path.join(loc, "snappy.ini")
    if not os.path.exists(file):
        raise FileNotFoundError(f"Cannot find snappy config folder {loc}")
    
    cfg = configparser.ConfigParser(
        interpolation = configparser.ExtendedInterpolation(),
        allow_no_value = True
    )

    cfg.optionxform = lambda s: s
    
    try:
        cfg.read(file)
    except Exception as err:
        raise RuntimeError("Cannot read config file") from err

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

    return True
