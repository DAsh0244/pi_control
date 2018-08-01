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
# from threading import Thread # , Lock
# noinspection PyUnresolvedReferences
from multiprocess import Process, Lock  # , Queue
# from multiprocessing import Lock, Queue, Process
from datetime import datetime
from time import perf_counter, sleep
from functools import wraps as _wraps
from inspect import signature as _signature
from typing import Dict, TextIO, Callable, FrozenSet, Iterable, Tuple  # , Union

from pubsub import pub

from version import version, prog_name

# pub.subscribe(callback, topic)

LOCK = Lock()
DEFAULT_DATA_LOC: str = '../DATA'
TOPICS: FrozenSet = frozenset({
    'actuator.position',
    'actuator.speed',
    'actuator.force',
    'thermocouple',
    'strain',
})

THERMOCOUPLE_NAMES: Tuple[str, ...] = ('sample', 'ambient', 'fluid')
COLUMNS: Dict[str, str] = {
    'actuator.position': 'time (s), position ({len_units})\n',
    'actuator.speed': 'time (s), speed (raw)\n',
    'actuator.force': 'time (s), force ({force_units}), local_temp (C), timestamp (ms since loadcell powerup)\n',
    'thermocouple': 'time (s), temperature (C), internal temperature (C)\n',
    'strain': 'time (s), strain (%)\n',
}

# def publish(topic):
#     if topic not in TOPICS:
#         raise ValueError(f'Unrecognized topic {topic}.\n'
#                          f'If trying to use a new topic, add it inside the DataRouter.py file')
#     def real_decorator(func):
#         @_wraps(func)
#         def wrapper(*args, **kwargs):
#             data = func(*args, **kwargs)
#             pub.sendMessage(topic, data=data)
#             print(topic, data)
#             return data
#         return wrapper
#     return real_decorator

PUBLISH_FUNCS = []


def add_to_poll(method):
    PUBLISH_FUNCS.append(method)


def publish(topic: str, keys: Tuple[str, ...]):
    if topic not in TOPICS:
        raise ValueError(f'Unrecognized topic {topic}.\n'
                         f'If trying to use a new topic, add it inside the DataRouter.py file')

    def real_decorator(func):
        fun_ret = _signature(func).return_annotation
        if len(keys) == 1:
            @_wraps(func)
            def wrapper(*args, **kwargs):
                datum = func(*args, **kwargs)
                pub.sendMessage(topic, data={keys[0]: datum})
                return datum
        elif len(str(fun_ret)[12:].split(',')) == len(keys):
            @_wraps(func)
            def wrapper(*args, **kwargs):
                datum = func(*args, **kwargs)
                pub.sendMessage(topic, data={k: v for k, v in zip(keys, datum)})
                return datum
        else:
            raise ValueError('Keys mismatch to function return annotation')
        return wrapper

    return real_decorator


def register_listeners(call_back, topics: Iterable):
    if any(topic not in TOPICS for topic in topics):
        bad_topics: Tuple[str] = tuple(topic for topic in topics if topic not in TOPICS)
        raise ValueError(f'Unrecognized topic(s) {bad_topics}.\n')
    for topic in topics:
        pub.subscribe(call_back, topic)


# data_queue = Queue()


# class DataWriter:
#     def __init__(self, outfiles: Union[Dict, None] = None):
#         self.outfiles = outfiles
#         # self.log()
#
#     def log(self, q: Queue):
#         while True:
#             record = q.get()
#             print(record[0], record[1])
#             self.outfiles[record[0]].write(record[1])
#
#     def __del__(self):
#         for file in self.outfiles.values():
#             file.write('\n')
#             file.close()
#
#
# record_keeper = DataWriter(outfiles=None)
# writer = Process(target=record_keeper.log, args=(data_queue,))
# writer.daemon = True
#

class DataLogger:
    log_header: str = f'# {prog_name},v{version}\n' \
                      '# log for:, {topic}\n' \
                      '# date:, {ts}\n' \
                      '# meta:, {meta}\n' \
                      '# comment:,\n'
    unpack_map: Dict[str, Callable] = {
        'actuator.position': '{0[ts]},{0[pos_info]}\n'.format,
        'actuator.speed': '{0[ts]},{0[speed]}\n'.format,
        'actuator.force': '{0[ts]},{0[force]},{0[local_temp]},{0[timestamp]}\n'.format,
        'thermocouple': '{0[ts]},{0[temp]},{0[internal_temp]}\n'.format,
        'strain': '{0[ts]},{0[strain]}\n'.format,
    }

    def __init__(self, config: Dict, outdir: str = None):
        self.start = perf_counter()
        self.topic_map: Dict[str, str] = {}
        self.logs: Dict[str, TextIO] = {}
        self.period = getattr(config, 'period', 0)
        if outdir is None:
            outdir = f'{DEFAULT_DATA_LOC}/{prog_name}_{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}'
            os.makedirs(outdir, exist_ok=True)
        for topic in TOPICS:
            if 'thermocouple' in topic:
                for meta in THERMOCOUPLE_NAMES:
                    topic_meta = '.'.join(filter(None, (topic, meta)))
                    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                    topic_file = f'{outdir}/{topic_meta}_{ts}.csv'
                    self.topic_map[topic_meta] = topic_file
                    self.logs[topic_meta] = open(topic_file, 'w')
                    # data_queue.put((topic_meta,
                    #                 self.log_header.format(topic=topic, ts=ts, meta=meta) + COLUMNS[topic].format(
                    #                     **config)))
                    self.logs[topic_meta].write(
                        self.log_header.format(topic=topic, ts=ts, meta=meta) + COLUMNS[topic].format(**config))

            else:
                ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                topic_file = f'{outdir}/{topic}_{ts}.csv'
                self.topic_map[topic] = topic_file
                self.logs[topic] = open(topic_file, 'w')
                # data_queue.put(
                #     (topic, self.log_header.format(topic=topic, ts=ts, meta='') + COLUMNS[topic].format(**config))
                # )
                self.logs[topic].write(
                    self.log_header.format(topic=topic, ts=ts, meta='') + COLUMNS[topic].format(**config))
        # record_keeper.outfiles = self.logs
        register_listeners(self.record_data, TOPICS)
        self.timerThread = Process(target=self.get_data, args=(self.period,))
        # self.timerThread = Thread(target=self.get_data, args=(self.period,))
        self.timerThread.daemon = True
        self.timerThread.start()
        self.start = perf_counter()

    def __del__(self):
        # self.timerThread.join()
        # while True:
        #     if data_queue.empty():
        #         break
        for file in self.logs.values():
            file.write('\n')
            file.close()

    @staticmethod
    def get_data(period):
        """
        force trigger publisher functions periodically to get data.
        :return:
        """
        time = perf_counter()
        while True:
            LOCK.acquire()
            print('\nGETTING FUNCTIONS\n')
            print(perf_counter() - time)
            time = perf_counter()
            # print(PUBLISH_FUNCS)
            for func in PUBLISH_FUNCS:
                # print(func)
                func()
            LOCK.release()
            sleep(period)

    def record_data(self, data, topic=pub.AUTO_TOPIC):
        # def record_data(self, data: Dict[str, Any], topic: str = pub.AUTO_TOPIC):
        topic = topic.getName()
        data['ts'] = perf_counter() - self.start  # datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        # print(topic, data)
        topic_meta = '.'.join(filter(None, (topic, data.pop('meta', ''))))
        # print('TOPIC META @@@@@@@@@@@@@@@@@@@@@@@@@@\n', topic_meta)
        # data_queue.put((topic_meta, self.unpack_map[topic](data)))
        self.logs[topic_meta].write(self.unpack_map[topic](data))
