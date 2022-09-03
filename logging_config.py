import logging
from logging.config import fileConfig


def configure():
    logging.config.fileConfig('logging_config.ini', disable_existing_loggers=False)
