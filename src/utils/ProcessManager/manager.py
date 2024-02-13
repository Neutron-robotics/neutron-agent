import logging
import os
import select
import shlex
import struct
import threading
from threading import Lock
import time
from .process import Process

def sbool(string):
    return True if string == "True" else False

# TODO: Add documentation

class ProcessManager:
    def __init__(self, monitor=False, log_frequency=30):
        self.log_frequency = log_frequency
        self.processes = []
        self._log_cpu = []
        self._log_memory = []
        self._monitor = monitor
        self._stop = False
        self.__mutex__ = Lock()

    def make_process(self, name, command, dir=".", id=None, initializer=None, pipe=False):
        process = Process(name, command, dir, id,
                          initializer=initializer, pipe=pipe)
        if process in self.processes:
            raise ValueError("Process already exists")
        print("MAKE Process :")
        print("-----------")
        print(f"Name: {process.name}")
        print(f"Id: {process.id}")
        print(f"dir: {process._dir}")
        print(f"command: {process.command}")
        print(f"initializer: {process.initializer}")
        print("-----------> Starting")
        process.start()
        self.add_process(process, self._monitor, self._monitor)
        return process.id

    def add_process(self, process, log_cpu=False, log_memory=False):
        """Adds a process to be managed.

        Args:
            process (Process): The process
            log_cpu (bool, optional): True if CPU usage should be tracked. Defaults to False.
            log_memory (bool, optional): True if memory usage should be tracked. Defaults to False.

        Returns:
            bool: True if process wasn't already added
        """

        if process in self.processes:
            return False
        self.processes.append(process)
        if log_cpu and process not in self._log_cpu:
            self._log_cpu.append(process)
        if log_memory and process not in self._log_memory:
            self._log_memory.append(process)
        return True

    def stop_process(self, id, flush=False):
        """Stop a proces"""
        for process in self.processes:
            if process.id == id:
                process.kill()
                if flush:
                    self.rem_process(process)
                return True
        return False

    def rem_process(self, process):
        """Removes a process"""
        self.processes.remove(process)
        if process in self._log_cpu:
            self._log_cpu.remove(process)
        if process in self._log_memory:
            self._log_memory.remove(process)

    def get_process(self, id):
        for process in self.processes:
            if process.id == id:
                return process
        return None

    @property
    def has_activeprocesses(self):
        return len(list(filter(lambda p: p.active, self.processes))) >= 1

    @property
    def log_period(self):
        return 60 / self.log_frequency

    def start(self):
        self._server_thread = threading.Thread(target=self.main_loop)
        self._server_thread.start()
        self._stop = False

    def stop(self):
        self._stop = True
        self._server_thread.join()
        for process in self.processes:
            process.kill()

    def main_loop(self):
        try:
            start = time.time()
            while not self._stop:
                if time.time() - start > 1:

                    start = time.time()
                    for process in self.processes:
                        with self.__mutex__:
                            if process.active:
                                process.process_stdout()
                                process.process_stderr()
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            print("[CORE] Process manager deinitializing")
            self._stop = True
