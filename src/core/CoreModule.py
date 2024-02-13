from modules.utils.ProcessManager import ProcessManager
from modules.utils.func_utils import load_configuration, get_time
import psutil
import os
import json
import requests
import threading
import time

class Core:
    def __init__(self, configuration):
        self.configuration = configuration
        self.name = self.configuration.get("name")
        self.type = self.configuration.get("type")
        self.connection = self.configuration.get("connection")
        self.modules = [x for x in self.configuration.get("modules", [])]
        try:
            self.modules = list(map(lambda x: {**x, 'configuration': load_configuration(x.get(
                'configuration'))} if type(x.get('configuration')) == str else x, self.modules))
        except Exception as e:
            print("[CORE] Error while initializing, existing program")
            print(str(e))
            exit(1)
        self.process_manager = ProcessManager()
        self.process_manager.start()
        self.operation_time = -1
        self.stop_event = threading.Event()


    def __del__(self):
        self.process_manager.stop()
        self.stop_status_thread()

    def make_process(self, processId):
        processInfos = [x for x in self.configuration.get(
            "modules", []) if x["id"] == processId]
        if (len(processInfos) == 0):
            raise ValueError("No valid process id")
        processInfo = processInfos[0]
        process_id = self.process_manager.make_process(processInfo.get('name'), processInfo.get(
            "command"), processInfo.get("path"), processId, initializer=processInfo.get("initializer"), pipe=True)
        process = self.process_manager.get_process(process_id)
        process.waitForReady()
        if (self.operation_time == -1 and len(self.process_manager.processes)):
            self.operation_time = get_time()
        return process_id

    def stop_process(self, processId, flush):
        success = self.process_manager.stop_process(processId, flush)
        if not (len(self.process_manager.processes)):
            self.operation_time = -1
        if not (success):
            raise ValueError("No valid process id")

    def get_enabled_modules(self):
        modules = [x for x in self.modules if x.get("enabled") == True]
        modules = map(lambda x: {"id": x.get("id"), "name": x.get("name"), "type": x.get(
            "type"), "framePackage": x.get("framePackage"), "configuration": x.get("configuration")}, modules)
        return modules

    def get_battery(self):
        battery = {
            "level": 80,
            "charging": False
        }
        return battery

    def enable_status_thread(self):
        # Create and start a thread that runs send_robot_status every 5 minutes
        self.status_thread = threading.Thread(target=self.status_thread_function)
        self.status_thread.start()

    def status_thread_function(self):
        while not self.stop_event.is_set():
            # Perform the status update
            self.send_robot_status()

            # Sleep for 5 minutes
            time.sleep(300)  # 300 seconds = 5 minutes

    def stop_status_thread(self):
        # Set the stop event to signal the thread to stop
        self.stop_event.set()

        # Wait for the thread to finish
        self.status_thread.join()

    def send_robot_status(self):
        if (self.configuration.get("linked") != True):
            print("Error: The robot must be linked to send status to the server")
            return

        serverUri = str(self.configuration.get('neutronCoreUri')) + '/agent/publishSystemInformation'
        systemInformations = {
                "status": self.status,
                "battery": self.get_battery(),
                "system": {
                    "cpu": self.cpu_usage,
                    "memory": self.memory_usage,
                },
                "location": {
                    "name": self.get_location()
                }
            }
        requestPayload = {
            "secretKey": self.configuration.get("secretKey"),
            "status": systemInformations
        }

        try:
            response = requests.post(serverUri, json=requestPayload)
            print("Published status to neutron server")
            if (response.status_code != 200):
                print("Error while publishing robot status")
                print(response.text)
        except Exception as e:
            print("[CORE] Error sending robot status")
            print(str(e))
        

    def update_configuration(self):
        try:
            myrobotics_root = os.environ.get("MYROBOTICS_ROOT")
            if not myrobotics_root:
                raise ValueError("MYROBOTICS_ROOT environment variable not set")

            config_path = os.path.join(myrobotics_root, "core.json")

            with open(config_path, "w") as config_file:
                json.dump(self.configuration, config_file, indent=4)

            print(f"[CORE] Configuration updated and saved to {config_path}")

        except Exception as e:
            print("[CORE] Error updating configuration")
            print(str(e))


    def get_location(self):
        return "Unknown"

    def get_processes_status(self):
        processes = []
        for i in self.process_manager.processes:
            processes.append(i.get_info())
        return processes

    @property
    def cpu_usage(self):
        return psutil.cpu_percent()

    @property
    def memory_usage(self):
        return psutil.virtual_memory().percent

    @property
    def status(self):
        if (len(self.process_manager.processes)):
            return "Operating"
        return "Online"
