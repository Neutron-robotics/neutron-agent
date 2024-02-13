from socketserver import ThreadingMixIn
from http.server import HTTPServer
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
 	"""Handle requests in a separate thread."""