from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class HttpRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args):
        get = args[0]
        post = args[1]
        self.routes = {
            "GET": get,
            "POST": post
        }
        BaseHTTPRequestHandler.__init__(self, *args[2:])

    # Used to answer CORS preflight requests
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        print("GET", self.path)
        if self.path in self.routes["GET"]:
            try:
                self.routes["GET"][self.path]()
            except Exception as e:
                print("GET - 500 - " + str(e))
                print(e)
                self.send_error(500, "Internal error happens")
        else:
            self.not_found()
        
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        self.body = json.loads(body.decode())
        print("POST", self.path)
        print("body", self.body)
        if self.path in self.routes["POST"]:
            try:
                self.routes["POST"][self.path]()
            except Exception as e:
                print("GET - 500 - " + str(e))
                print(e)
                self.send_error(500, "Internal error happens")
        else:
            self.not_found()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def success(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def not_found(self):
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def send_error(self, code, message):
        self.send_response(code)
        if message:
            self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        if message:
            self.wfile.write(message.encode())

    