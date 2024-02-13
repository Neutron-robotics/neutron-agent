from utils.HttpRequestHandler import HttpRequestHandler

class CoreHttpHandler(HttpRequestHandler):
    def __init__(self, *args):
        get = {
            "/robot/status": self.robot_status,
            "/robot/configuration": self.robot_configuration
        }
        post = {
            "/start": self.start_process,
            "/stop": self.stop_process,
        }
        HttpRequestHandler.__init__(self, get, post, *args)

    def robot_status(self):
        processes_status = self.server.core.get_processes_status()
        status = {
            "battery": -1,
            "cpu": self.server.core.cpu_usage,
            "memory": self.server.core.memory_usage,
            "operationTime": self.server.core.operation_time,
            "modules": list(processes_status)
        }
        self.send_json(status)

    def robot_configuration(self):
        modules = self.server.core.get_enabled_modules()
        configuration = {
            "robot": {
                "battery": -1,
                "name": self.server.core.name,
                "type": self.server.core.type,
                "status": self.server.core.status,
                "connection": self.server.core.connection,
                "modules": list(modules) #now test (and remove me)
            }
        }
        self.send_json(configuration)

    def start_process(self):
        try:
            process_id = self.server.core.make_process(self.body.get("processId"))
            self.send_json(data={"processId": process_id})
        except ValueError as e:
            print("ERROR " +str(e))
            self.send_error(400, str(e))
    
    def stop_process(self):
        try:
            process_id = self.body.get("processId")
            flush = self.body.get("flush")
            self.server.core.stop_process(process_id, flush)
            self.success()
        except ValueError as e:
            self.send_error(400, str(e))
    