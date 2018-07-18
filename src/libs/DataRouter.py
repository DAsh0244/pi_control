#! /usr/bin/env python
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
pi_control
DataRouter.py
Author: Danyal Ahsanullah
Date: 7/17/2018
Copyright (c):  2018 Danyal Ahsanullah
License: N/A
Description: constructs for forwarding and logging various data values
"""

import os
# import os.path as osp
from functools import wraps
from datetime import datetime
from typing import Dict, TextIO, Callable, Any, Set, Iterable, List

from pubsub import pub

from version import version, prog_name

# pub.subscribe(callback, topic)

DEFAULT_DATA_LOC: str = '../../DATA'
TOPICS: Set = {
    'actuator.position',
    'actuator.speed',
    'actuator.force',
    'thermocouple.1',
    'thermocouple.2',
    'thermocouple.3',
    'strain',
}
THERMOCOUPLE_NAMES: Dict[str, str] = {'1': 'sample', '2': 'ambient', '3': 'fluid'}
COLUMNS: Dict[str, str] = {
    'actuator.position': 'time (s), position ({units})',
    'actuator.speed': 'time (s), speed (raw)',
    'actuator.force': 'time (s), force ({units}), local_temp (C), timestamp (ms since loadcell powerup)',
    'thermocouple.1': 'time (s), temperature (C), internal temperature (C)',
    'thermocouple.2': 'time (s), temperature (C), internal temperature (C)',
    'thermocouple.3': 'time (s), temperature (C), internal temperature (C)',
    'strain': 'time (s), strain (%)',
}


def publish(topic):
    if topic not in TOPICS:
        raise ValueError(f'Unrecognized topic {topic}.\n'
                         f'If trying to use a new topic, add it inside the DataRouter.py file')
    def real_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = func(*args, **kwargs)
            pub.sendMessage(topic, data=data)
            print(topic, data)
            return data
        return wrapper
    return real_decorator


def __listen(topics: Iterable):
    if any(topic not in TOPICS for topic in topics):
        bad_topics: List[str] = [topic for topic in topics if topic not in TOPICS]
        raise ValueError(f'Unrecognized topic(s) {bad_topics}.\n')

    def real_decorator(func):
        for topic in topics:
            pub.subscribe(func, topic)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return real_decorator


def register_listeners(call_back, topics: Iterable):
    if any(topic not in TOPICS for topic in topics):
        bad_topics: List[str] = [topic for topic in topics if topic not in TOPICS]
        raise ValueError(f'Unrecognized topic(s) {bad_topics}.\n')
    for topic in topics:
        pub.subscribe(call_back, topic)


class DataLogger:
    log_header: str = f'# {prog_name} : v{version}\n' \
                      '# log for: {topic}\n' \
                      '# date: {ts}\n' \
                      '# meta: {meta}\n'
    unpack_map: Dict[str, Callable] = {
        'actuator.position': '{0["ts"]},{0["pos_info"]}\n'.format,
        'actuator.speed': '{0["ts"]},{0["speed"]}\n'.format,
        'actuator.force': '{0["ts"]},{0["force"]},{0["local_temp"]},{0["timestamp"]}\n'.format,
        'thermocouple.1': '{0["ts"]},{0["temp"]},{0["internal_temp"]}\n'.format,
        'thermocouple.2': '{0["ts"]},{0["temp"]},{0["internal_temp"]}\n'.format,
        'thermocouple.3': '{0["ts"]},{0["temp"]},{0["internal_temp"]}\n'.format,
        'strain': '{0["ts"]},{0["strain"]}\n'.format,
    }

    def __init__(self, outdir: str = None):
        self.topic_map: Dict[str, str] = {}
        self.logs: Dict[str, TextIO] = {}
        if outdir is None:
            outdir = f'{DEFAULT_DATA_LOC}/{prog_name}_{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}'
            os.makedirs(outdir, exist_ok=True)
        for topic in TOPICS:
            if 'thermocouple' in topic:
                meta = THERMOCOUPLE_NAMES[topic.split('.')[1]]
            else:
                meta = ''
            pub.subscribe(self.record_data, topic)
            ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            topic_file = f'{outdir}/{topic}_{ts}.txt'
            self.topic_map[topic] = topic_file
            self.logs[topic] = open(topic_file, 'w')
            self.logs[topic].write(self.log_header.format(topic=topic, ts=ts, meta=meta) + COLUMNS[topic])
        register_listeners(self.record_data, TOPICS)

    def __del__(self):
        for file in self.logs.values():
            file.close()

    def record_data(self, data: Dict[str, Any], topic: str = pub.AUTO_TOPIC):
        data['ts'] = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.logs[topic].write(self.unpack_map[topic](data))


if __name__ == '__main__':
    @publish('asdfg')
    def wrapped_fun():
        print('wrapped_function')
        return 4


    Logger = DataLogger()
    wrapped_fun()
