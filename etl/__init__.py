import json
from pathlib import Path
from typing import List


class TimestampedResult:
    def __init__(self, timestamp: str, result=None, error: str = None):
        self.timestamp = timestamp
        self.result = result
        self.error = error

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)


def sort_unique_ts_history(ts_history: List[dict]) -> List[dict]:
    unique_ts_history = {json.dumps(d, sort_keys=True) for d in ts_history}
    unique_ts_history = [json.loads(d) for d in unique_ts_history]
    unique_ts_history = sorted(unique_ts_history, key=lambda e: e.get('timestamp', None))
    return unique_ts_history


def compare_ts_history_with_current(ts_history: List[dict], cur_result: dict, cur_ts: str, logger) -> bool:
    if ts_history:
        # Compare (excluding the timestamp key) the last entry to this current one
        prev_result = ts_history[len(ts_history) - 1].copy()
        prev_result.pop('timestamp', None)
        if cur_result == prev_result:
            logger.debug('No changes; ignoring {}'.format(cur_result))
            return False

    # Change found...append entry to history
    cur_ts_result = cur_result.copy()
    cur_ts_result['timestamp'] = cur_ts
    ts_history.append(cur_ts_result)
    return True


def finalize_target_file(target_file: Path, logger) -> bool:
    if not target_file.exists():
        return False

    with target_file.open(mode='r') as json_file:
        logger.debug('Reading {}'.format(target_file))
        ts_history = json.load(json_file)

    # Remove duplicates and sort
    unique_ts_history = sort_unique_ts_history(ts_history)
    if ts_history == unique_ts_history:
        return False

    with target_file.open(mode='w') as json_file:
        logger.debug('Updating {} from {} to {} entries'.format(target_file, len(ts_history), len(unique_ts_history)))
        json.dump(unique_ts_history, fp=json_file, default=lambda o: o.__dict__, sort_keys=True, indent=2)


def finalize_target_files(root_path: Path, target_file_patterns: list, logger):
    # Sort and remove duplicates from target file(s)
    for target_file_pattern in target_file_patterns:
        target_files = sorted(root_path.glob(target_file_pattern))
        logger.info('Finalizing {} target files from {}/{}'.format(len(target_files), root_path, target_file_pattern))
        for target_file in target_files:
            changed = finalize_target_file(target_file, logger)
            logger.debug('Finalized {}; changed?={}'.format(target_file, changed))
