from modules.utils.ProcessManager import ProcessManager
from modules.utils.func_utils import load_configuration, get_time
import psutil
import os
import json
import requests
import threading
import time
import hashlib
import copy
import subprocess

class Core:
    def __init__(self, configuration, is_deamon=False):
        self.is_deamon = is_deamon
        self.stop_event = threading.Event()
        self.status_thread = None
        self.configuration = configuration
        self.name = self.configuration.get("name")
        self.type = self.configuration.get("type")
        self.connection = self.configuration.get("connection")
        self.context = load_configuration(f"contexts/{configuration.get('context').get('type')}.json")
        self.context["process"]["processId"] = None
        self.parts = copy.deepcopy(self.configuration.get("parts", []))
        self.process_manager = None

    def start_robot(self, processesId = []):
        #1. Configure for session
        self.process_manager = ProcessManager()
        self.process_manager.start()
        self.operation_time = -1

        #2. start the context
        contextId = self.context["process"].get("processId")
        if (contextId == None):
            self.start_context()
        else:
            print("Context already started")

        #3. start robot processes
        parts = self.parts if processesId == [] else [part for part in self.parts if part['id'] in processesId]
        for part in parts:
            command = f"ros2 run {part.get('ros2Package')} {part.get('ros2Node')}"
            processId = self.process_manager.make_process(
                part.get("name"),
                command,
                ".",
                part.get("id"),
                part.get("initializer", None),
                True
            )
            part["processId"] = processId
            self.send_robot_status()

    def start_context(self):
        source_path = self.context["process"].get("sourcePath")

        # Source content if the sourcePath is defined in the context configuration
        if (source_path):
            try:
                subprocess.run(['source', source_path], shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error sourcing context: {e}")

        processId = self.process_manager.make_process(
            self.context["process"].get("name"),
            self.context["process"].get("command"),
            self.context["process"].get("path"),
            self.context["process"].get("id"),
            self.context["process"].get("initializer"),
            True
        )
        context = self.process_manager.get_process(processId)
        context.waitForReady()
        self.context["process"]["processId"] = processId
        self.send_robot_status()

    def stop_robot(self):
        # Stop robot processes
        for part in self.parts:
            processId = part.get("processId")
            if (processId == None):
                continue
            self.process_manager.stop_process(processId, True)
            part["processId"] = None

        # Stop context
        processId = self.context["process"]["processId"]
        if (processId != None):
            self.process_manager.stop_process(processId, True)
            self.context["process"]["processId"] = None

        self.process_manager.stop()
        self.send_robot_status()

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

            # Sleep for 200 seconds
            time.sleep(200)

    def stop_status_thread(self):
        if (self.status_thread == None):
            return

        # Set the stop event to signal the thread to stfop
        self.stop_event.set()

        # Wait for the thread to finish
        self.status_thread.join()

    def get_network_infos(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        hostname = s.getsockname()[0]
        s.close()
        return hostname

    def calculate_hash(self):
        obj = {
            "name": self.configuration["name"],
            "context": self.configuration["context"],
            "parts": self.configuration["parts"]
        }
        json_str = json.dumps(obj, separators=(',', ':'))
        hash = hashlib.sha256(json_str.encode()).hexdigest()
        return hash

    def send_robot_status(self):
        if (self.configuration.get("linked") != True):
            print("Error: The robot must be linked to send status to the server")
            return

        serverUri = str(self.configuration.get('neutronCoreUri')) + '/agent/publishSystemInformation'
        systemInformations = self.build_status_message()
        requestPayload = {
            "secretKey": self.configuration.get("secretKey"),
            "status": systemInformations
        }

        try:
            response = requests.post(serverUri, json=requestPayload)
            body = response.json()
            print("Published status to neutron server")
            if (body.get("configuration")):
                self.pull_configuration(body["configuration"])
            if (response.status_code != 200):
                print("Error while publishing robot status")
                print(response.text)
        except Exception as e:
            print("[CORE] Error sending robot status")
            print(str(e))
        

    def pull_configuration(self, configuration):
        print("Pulling new configuration", configuration)
        self.configuration["context"] = configuration["context"]
        self.configuration["parts"] = configuration["parts"]
        self.configuration["name"] = configuration["name"]
        self.update_configuration()
        self.context = load_configuration(f"contexts/{configuration.get('context').get('type')}.json")

    def update_configuration(self):
        try:
            neutron_root = os.environ.get("NEUTRON_ROOT")
            if not neutron_root:
                raise ValueError("NEUTRON_ROOT environment variable not set")

            config_path = os.path.join(neutron_root, "neutron.json")

            with open(config_path, "w") as config_file:
                json.dump(self.configuration, config_file, indent=4)

            print(f"[CORE] Configuration updated and saved to {config_path}")

        except Exception as e:
            print("[CORE] Error updating configuration")
            print(str(e))


    def get_location(self):
        return "Unknown"

    def get_processes_status(self):
        if (self.is_deamon):
            return self.get_processes_status_as_deamon

        if (self.process_manager == None):
            return []

        processes = []
        for process in self.process_manager.processes:
            if (process.id == self.context["process"].get("processId", '')):
                continue
            process_infos = process.get_info()
            processes.append(process_infos)
        return processes

    def get_context_status(self):
        if (self.is_deamon):
            return self.get_context_status_as_deamon

        if (self.process_manager == None):
            return None

        for process in self.process_manager.processes:
            if (process.id == self.context["process"].get("processId", '')):
                context_infos = process.get_info()
                context_infos["port"] = self.context["process"]["port"]
                return context_infos
        return None

    def build_status_message(self):
        systemInformations = {
                "status": self.status,
                "battery": self.get_battery(),
                "system": {
                    "cpu": self.cpu_usage,
                    "memory": self.memory_usage,
                },
                "location": {
                    "name": self.get_location()
                },
                "hash": self.calculate_hash(),
                "network": {
                    "hostname": self.get_network_infos()
                },
                "processes": self.get_processes_status(),
                "context": self.get_context_status()
            }
        return systemInformations

    @property
    def cpu_usage(self):
        return psutil.cpu_percent()

    @property
    def memory_usage(self):
        return psutil.virtual_memory().percent

    @property
    def status(self):
        if (self.is_deamon):
            return self.status_as_deamon
        elif (self.process_manager and len(self.process_manager.processes)):
            return "Operating"
        return "Online"

    @property
    def agent_server_base_url(self):
        if (not self.is_deamon):
            raise Exception("Usage of agent url should be when the Core module is used as a deamon")
        return 'http://localhost:' + str(self.configuration.get('port'))

    @property
    def status_as_deamon(self):
        status = "Online"
        try:
            response = requests.get(f"{self.agent_server_base_url}/robot/status")
            if (response.status_code != 200):
                status = "Unknown"
                return
            modules = response.json().get("modules")
            if (modules != []):
                status = "Operating"
        except:
            status = "Offline"
        return status

    @property
    def get_context_status_as_deamon(self):        
        try:
            response = requests.get(f"{self.agent_server_base_url}/robot/status")
            if (response.status_code != 200):
                status = "Could not fetch context informations"
                return
            context = response.json().get("context")
        except Exception as e:
            context = "Could not fetch context informations (ex)"
        return context

    @property
    def get_processes_status_as_deamon(self):
        try:
            response = requests.get(f"{self.agent_server_base_url}/robot/status")
            if (response.status_code != 200):
                processes = "Could not fetch processes informations"
                return processes
            processes = response.json().get("processes")
        except Exception as e:
            processes = "Could not fetch processes informations (ex)"
        return processes