import json
import socket
from datetime import datetime
from pathlib import Path
from typing import List

from hnap import HNAPDevice


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        result = s.getsockname()
        return result[0]
    finally:
        s.close()


def build_unique_stats_path(device: HNAPDevice, stat_type: str) -> Path:
    unique = datetime.now().strftime('%Y%m%d_%H%M%S')
    return Path('devices', device.device_id, stat_type, '{}.json'.format(unique))


def build_stats_history_path(device: HNAPDevice, stat_type: str) -> Path:
    return Path('devices', device.device_id, stat_type, '{}.json'.format(stat_type))


def get_stats_history(device: HNAPDevice, stat_type: str, logger) -> List[dict]:
    stats_file = build_stats_history_path(device, stat_type)
    if not stats_file.exists():
        logger.debug('history: {} not found'.format(stats_file))
        return list()

    with stats_file.open() as json_file:
        history = json.load(json_file)
    logger.debug('history: Found {} entries in {}'.format(len(history), stats_file))
    return history


def set_stats_history(device: HNAPDevice, stat_type: str, history: List[dict], logger):
    stats_file = build_stats_history_path(device, stat_type)
    with stats_file.open(mode='w') as json_file:
        logger.debug('history: Setting {} with {} entries'.format(stats_file, len(history)))
        json.dump(history, fp=json_file, default=lambda o: o.__dict__, sort_keys=True, indent=2)


def append_stats_history(device: HNAPDevice, stat_type: str, entries_to_append: List[dict], logger):
    history = get_stats_history(device, stat_type, logger)
    set_stats_history(device, stat_type, history + entries_to_append, logger)
