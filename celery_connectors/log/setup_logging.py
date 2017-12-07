import os
import json
import logging.config


def get_logger(logger):
    """Get logger by name."""
    if isinstance(logger, string_t):
        logger = logging.getLogger(logger)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
# end of get_logger


def setup_logging(default_level=logging.INFO,
                  default_path="{}/logging.json".format(
                      os.getenv("LOG_DIR",
                                os.path.dirname(os.path.realpath(__file__))).strip().lstrip()),
                  env_key='LOG_CFG'):

    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
# end of setup_logging
