import json
import os
import time

MYROBOTICS_ROOT = "MYROBOTICS_ROOT"

def load_configuration(path, with_prefix=True):
	prefix = ""
	if with_prefix:
		prefix = os.environ.get(MYROBOTICS_ROOT, "")
		if (prefix == ""):
			print("MYROBOTICS_ROOT environment variable not set")
			raise Exception("MYROBOTICS_ROOT environment variable not set")
	file_path = os.path.join(prefix, path)
	
	if not (os.access(file_path, os.F_OK)):
		raise OSError(f"Configuration {file_path} does not exist")
	with open(file_path) as json_file:
		return json.load(json_file)

def get_time():
	return int(round(time.time() * 1000))