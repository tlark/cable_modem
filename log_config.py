import logging
from logging import config

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        '': {
            'handlers': ['fileHandler'],
            'level': 'INFO'
        },
        'monitor': {
            'handlers': ['fileHandler'],
            'level': 'INFO',
            'propagate': False
        },
        'transformer': {
            'handlers': ['fileHandler'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'handlers': {
        'consoleHandler': {
            'level': 'DEBUG',
            'formatter': 'consoleFormatter',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'fileHandler': {
            'level': 'DEBUG',
            'formatter': 'fileFormatter',
            'class': 'logging.FileHandler',
            'mode': 'a',
            'filename': 'cable_modem.log'
        }
    },
    'formatters': {
        'fileFormatter': {
            'format': '%(asctime)s.%(msecs)03d %(levelname)-8s %(name)-16s: %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
            'class': 'logging.Formatter'
        },
        'consoleFormatter': {
            'format': '%(asctime)s.%(msecs)03d %(levelname)-8s %(name)-16s: %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
            'class': 'logging.Formatter'
        },
    },
}


def configure(log_filename):
    LOG_CONFIG['handlers']['fileHandler']['filename'] = log_filename
    logging.config.dictConfig(LOG_CONFIG)
