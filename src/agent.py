import argparse
from utils.func_utils import load_configuration
from utils.threaded_http_server import ThreadedHTTPServer
from core.CoreHttpHandler import CoreHttpHandler
from core.CoreModule import Core
from core.install import create_install_path, copy_configuration, update_bashrc, add_neutron_alias
import requests
import time
import os
import subprocess

def run_setup_script():
    neutron_root = os.getenv('NEUTRON_ROOT')
    
    if not neutron_root:
        print("Error: NEUTRON_ROOT environment variable is not set.")
        return

    setup_script_path = os.path.join(neutron_root, 'setup.sh')
    if not os.path.exists(setup_script_path):
        print(f"Error: setup.sh script not found at {setup_script_path}.")
        return

    try:
        subprocess.run(['bash', setup_script_path], check=True)
        print(f"Successfully ran {setup_script_path}.")
    except subprocess.CalledProcessError as e:
        print(f"Error running setup script: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def run_server(configuration):
    port = configuration.get("port")
    server = ThreadedHTTPServer(('0.0.0.0', port), CoreHttpHandler)
    server.configuration = configuration
    server.core = Core(configuration=configuration)
    server.core.enable_status_thread()
    server.serve_forever()

    self.stop_status_thread()


def custom_link_function(configuration):
    core = Core(configuration, True)
    key = input("Enter the key: ")
    if (len(key) != 36):
        print("Invalid key")
        return
    
    url = f"{configuration.get('neutronCoreUri')}/agent/link"
    response = requests.post(url, {"secretKey": key})

    if response.status_code == 200:
        core.configuration["secretKey"] = key
        core.configuration["linked"] = True
        core.update_configuration()
        print("Linking successful")
    else:
        print(f"Error linking: {response.text}")

def install_neutron():
    repo_path = os.path.abspath(os.path.dirname(__file__))

    try:
        install_path = create_install_path()
        copy_configuration(install_path)
        update_bashrc(install_path)
        add_neutron_alias(repo_path)
    except Exception as e:
        print(e)
        return

def custom_status_function(configuration):
    core = Core(configuration, True)
    status_message = core.build_status_message()

    formatted_output = (
        f"Status: {status_message['status']}\n"
        f"Battery: {status_message['battery']}\n"
        f"  Level: {status_message['battery']['level']}\n"
        f"  Charging: {status_message['battery']['charging']}\n"
        f"System: {status_message['system']}\n"
        f"  CPU: {status_message['system']['cpu']}\n"
        f"  Memory: {status_message['system']['memory']}\n"
        f"Location: {status_message['location']}\n"
        f"  Name: {status_message['location']['name']}\n"
        f"Hash: {status_message['hash']}\n"
        f"Network: {status_message['network']}\n"
        f"  Hostname: {status_message['network']['hostname']}\n"
        f"Processes: {status_message['processes']}\n"
        f"Context: {status_message['context']}"
    )

    print(formatted_output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='The neutron agent is responsible for installing and managing the services for the robot.')    

    parser.add_argument('--run', action='store_true', help='Run the server')
    parser.add_argument('--link', action='store_true', help='Link the robot with the Neutron platform')
    parser.add_argument('--status', action='store_true', help='Display robot status')
    parser.add_argument('--install', action='store_true', help='Install neutron agent')

    args = parser.parse_args()

    if (args.install):
        install_neutron()
    elif args.run:
        print("Starting neutron agent")
        configuration = load_configuration("neutron.json")
        run_setup_script()
        run_server(configuration)
    elif args.link:
        configuration = load_configuration("neutron.json")
        custom_link_function(configuration)
    elif args.status:
        configuration = load_configuration("neutron.json")
        custom_status_function(configuration)
    else:
        parser.print_help()
    exit(0)
