from utils.HttpRequestHandler import HttpRequestHandler
import json

class CoreHttpHandler(HttpRequestHandler):
    def __init__(self, *args):
        get = {
            "/robot/status": self.robot_status,
        }
        post = {
            "/robot/start": self.start_robot,
            "/robot/stop": self.stop_robot,
        }
        HttpRequestHandler.__init__(self, get, post, *args)

    def robot_status(self):
        status_message = self.server.core.build_status_message()

        self.send_json(status_message)

    def start_robot(self):
        try:
            processedId = self.body.get('processesId', [])
            self.server.core.start_robot(processedId)
            self.success()
        except ValueError as e:
            print("ERROR " +str(e))
            self.send_error(400, str(e))

    def stop_robot(self):
        try:
            self.server.core.stop_robot()
            self.success()
        except ValueError as e:
            print("ERROR " +str(e))
            self.send_error(400, str(e))

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
    