import argparse
import json
import logging
import os
from datetime import datetime, timedelta
from time import sleep

import schedule

import log_config
from common import get_local_ip, build_unique_stats_path
from devices import create_device
from hnap import HNAPDevice
from models import EventLogEntry

log_config.configure('monitor.log')
logger = logging.getLogger('monitor')

# Associate function calls with single word actions
actions = {'summary': 'get_connection_summary',
           'events': 'get_events',
           'details': 'get_connection_details'}


class JobRunSummary:
    def __init__(self, name: str, succeeded=True):
        self.name = name
        self.started_at = datetime.now()
        self.completed_at = None
        self.succeeded = succeeded

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self.__dict__)


class DeviceMonitor:
    def __init__(self, scheduler: schedule.Scheduler, check_interval: timedelta = None, device: HNAPDevice = None):
        self.scheduler = scheduler
        self.interval = int(check_interval.total_seconds()) if check_interval else 30
        self.device = device
        self.all_jobs_history = list()
        self.check_job = None

    def __str__(self):
        if self.check_job:
            job_status = 'Running (next at {}): {}'.format(self.check_job.next_run, self.check_job)
        else:
            job_status = 'Idle'
        return '({}, #history={}, device={})'.format(job_status, len(self.all_jobs_history), self.device)

    def start(self):
        if self.check_job:
            logger.debug('Device monitor start (already started): {}'.format(self))
            return

        self.check_job = self.scheduler.every(self.interval).seconds.do(ping, device_monitor=self)
        self.check_job.run()
        logger.info('Device monitor started (next at {}): {}'.format(self.check_job.next_run, self))

    def cancel(self):
        if not self.check_job:
            logger.debug('Device monitor cancel (not running): {}'.format(self))
            return
        self.scheduler.cancel_job(self.check_job)
        self.check_job = None
        logger.info('Device monitor canceled: {}'.format(self))


def log_client_event(device: HNAPDevice, level: int, desc: str):
    ts = datetime.now()
    event = EventLogEntry(timestamp=ts, priority=device.to_event_priority(level),
                          desc='(Client {}): {}'.format(get_local_ip(), desc))
    event_json = json.loads(json.dumps(event, default=lambda o: o.__dict__))

    # Make this look like the other event files
    timestamped_json_result = {'timestamp': ts.isoformat(), 'result': [event_json]}
    stats_file = build_unique_stats_path(device, 'events')
    with stats_file.open(mode='w') as file:
        file.write(json.dumps(timestamped_json_result, default=lambda o: o.__dict__))


def setup(device_id: str, device_attrs: dict, action_ids: list, note: str) -> HNAPDevice:
    device = create_device(device_id)
    device.login(device_attrs['scheme'], device_attrs['host'], device_attrs['username'], device_attrs['password'])

    # Create directories to hold JSON results and add any specified note to the README file
    for action_id in action_ids:
        path = 'devices/{}/{}'.format(device_id, action_id)
        os.makedirs(path, exist_ok=True)
        if note:
            with open('{}/README.txt'.format(path), 'a') as readme_file:
                readme_file.write('{}: {}\n'.format(datetime.now().strftime('%Y%m%d %H%M%S'), note))
    try:
        # Populate device info
        device.get_device_info()
    except NotImplementedError:
        pass

    logger.info('setup complete for {}'.format(device))
    return device


def get_stats(stat_ids: list, device_monitor: DeviceMonitor) -> None:
    job_run_summary = JobRunSummary('get_stats')
    device = device_monitor.device
    try:
        for stat_id in stat_ids:
            stat_name = actions.get(stat_id, None)
            if not stat_name:
                logger.error('Stat "{}" not supported for {}'.format(stat_id, device))
                continue

            stat_func = getattr(device, stat_name, None)
            if not stat_func:
                logger.error('Stat function "{}" not supported for {}'.format(stat_name, device))
                continue

            try:
                stats_file = build_unique_stats_path(device, stat_id)
                json_result = stat_func()
                timestamped_json_result = {'timestamp': datetime.now().isoformat(), 'result': json_result}
                with stats_file.open(mode='w') as file:
                    file.write(json.dumps(timestamped_json_result, default=lambda o: o.__dict__))
                logger.debug('Get {} stats complete for {}; results in {}'.format(stat_id, device, stats_file))
            except Exception as e:
                msg = 'Get {} stats FAILED ({}) for {}'.format(stat_id, e, device)
                logger.warning(msg)
                log_client_event(device, logging.WARNING, msg)
                raise e
        logger.info('Get stats complete for {}'.format(device))
        device_monitor.cancel()
    except Exception:
        job_run_summary.succeeded = False
        device_monitor.start()
    finally:
        job_run_summary.completed_at = datetime.now()
        device_monitor.all_jobs_history.append(job_run_summary)


def reboot(device_monitor: DeviceMonitor):
    job_run_summary = JobRunSummary('reboot')
    device = device_monitor.device
    job_run_history = device_monitor.all_jobs_history
    try:
        logger.info('reboot; job history={}'.format([(e.name, e.succeeded) for e in job_run_history]))
        log_client_event(device, logging.CRITICAL, 'Rebooting {}'.format(device))
        device.reboot()
        # Pause monitoring while the device reboots
        logger.info('Waiting 60 seconds for {}'.format(device))
        sleep(60)
    except Exception as e:
        job_run_summary.succeeded = False
        logger.error('reboot FAILED ({}) for {}'.format(e, device))
    finally:
        job_run_history.clear()
        job_run_summary.completed_at = datetime.now()
        job_run_history.append(job_run_summary)
    logger.info('reboot complete for {}'.format(device))


def ping(device_monitor: DeviceMonitor):
    job_run_summary = JobRunSummary('ping')
    device = device_monitor.device
    job_run_history = device_monitor.all_jobs_history
    try:
        device.ping()
    except Exception as e:
        msg = 'ping FAILED ({}) for {}'.format(e, device)
        logger.warning(msg)
        log_client_event(device, logging.WARNING, msg)
        job_run_summary.succeeded = False
        device.invalidate_session()
    finally:
        job_run_summary.completed_at = datetime.now()
        job_run_history.append(job_run_summary)
    logger.debug('ping complete for {}'.format(device))

    if job_run_summary.succeeded and is_reboot_recommended(device, job_run_history):
        reboot(device_monitor)


def is_reboot_recommended(device: HNAPDevice, job_run_history: list) -> bool:
    # Determine if a reboot should be done based on job history:
    # - If there are 3+ failures between 2 successful runs, then a reboot is recommended
    failed_threshold = 3
    failed = 0
    succeeded = 0
    for job_run_entry in reversed(job_run_history):
        logger.debug('is_reboot_recommended: Processing {} for {}'.format(job_run_entry, device))
        if job_run_entry.name == 'reboot':
            break
        if job_run_entry.succeeded:
            succeeded += 1
            # If this is the 2nd success after any failures, we're done
            if succeeded == 2 and failed > 0:
                break
        elif succeeded > 0:
            failed += 1
            # Ignore succeeded ones before the first failure
            succeeded = 1

    recommended = succeeded >= 2 and failed >= failed_threshold
    logger.debug(
        'is_reboot_recommended? {}: #succeeded={}, #failed={} for {}'.format(recommended, succeeded, failed, device))
    if recommended:
        msg = 'Reboot is recommended since {} failures have occurred'.format(failed)
        logger.info(msg)
        log_client_event(device, logging.INFO, msg)

    return recommended


def main():
    with open('devices/devices.json') as devices_file:
        supported_devices = json.load(devices_file)

    wanted_stats = ['summary', 'events', 'details']

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--note', required=False, help='Add this note to the stats README file')
    parser.add_argument('--reboot_times', default=['04:00'], nargs='*',
                        help='Times of day that an automatic reboot should occur')
    parser.add_argument('--check_interval', type=int, choices=range(30, 61), metavar='[30-60]', default=30,
                        help='Check every S seconds')
    parser.add_argument('--stats_interval', type=int, choices=range(1, 6), metavar='[1-5]', default=5,
                        help='Get stats every M minutes')
    parser.add_argument('device_id', choices=supported_devices.keys())
    args = parser.parse_args()

    device_attrs = supported_devices.get(args.device_id)
    stat_ids = [a for a in wanted_stats if a in device_attrs['supported_actions']]

    device = setup(args.device_id, device_attrs, stat_ids, args.note)

    scheduler = schedule.Scheduler()
    device_monitor = DeviceMonitor(scheduler, timedelta(seconds=args.check_interval), device)
    stats_job = scheduler.every(args.stats_interval).minutes.at(':00').do(get_stats, stat_ids=stat_ids,
                                                                          device_monitor=device_monitor)
    logger.info('Stats schedule (next at {}): {}'.format(stats_job.next_run, stats_job))

    # Reboot the device N times daily
    reboot_scheduler = schedule.Scheduler()
    for reboot_time in args.reboot_times:
        job = reboot_scheduler.every().day.at(reboot_time).do(reboot, device_monitor=device_monitor)
        logger.info('Reboot schedule (next at {}): {}'.format(job.next_run, job))

    try:
        scheduler.run_all()
        while True:
            scheduler.run_pending()
            reboot_scheduler.run_pending()
            sleep(5)
    except KeyboardInterrupt:
        device.logout()
        pass


if __name__ == '__main__':
    main()
