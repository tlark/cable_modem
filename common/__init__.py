import json
import socket
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


def build_stats_file_path(device: HNAPDevice, stat_type: str) -> Path:
    return Path('devices', device.device_id, stat_type, '{}.json'.format(stat_type))


def get_stats_history(device: HNAPDevice, stat_type: str, logger) -> List[dict]:
    stats_file = build_stats_file_path(device, stat_type)

    history = list()
    if stats_file.exists():
        with stats_file.open() as json_file:
            history = json.load(json_file)
    logger.debug('history: Found {} entries in {}'.format(len(history), stats_file))
    return history


def append_stats_history(device: HNAPDevice, stat_type: str, entries_to_append: List[dict], logger):
    history = get_stats_history(device, stat_type, logger)
    history = history + entries_to_append

    stats_file = build_stats_file_path(device, stat_type)
    with stats_file.open(mode='w') as json_file:
        logger.debug('history: Updating {} with {} entries'.format(stats_file, len(history)))
        json.dump(history, fp=json_file, default=lambda o: o.__dict__, sort_keys=True, indent=2)
