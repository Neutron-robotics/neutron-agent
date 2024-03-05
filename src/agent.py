import argparse
from utils.func_utils import load_configuration
from utils.threaded_http_server import ThreadedHTTPServer
from core.CoreHttpHandler import CoreHttpHandler
from core.CoreModule import Core
import requests
import time
import os
import shutil

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
    install_path = input("Enter folder installation path (~/.neutron):").strip()
    if not install_path:
        install_path = os.path.expanduser("~/.neutron")

    # Check if the install path already exists
    if os.path.exists(install_path):
        response = input(f"The installation path '{install_path}' already exists. Do you want to continue? (y/n): ").strip().lower()
        if response != 'y':
            print("Installation aborted.")
            return
    
    config_base_path = './configuration/'
    config_files = ['neutron.json', 'contexts/ros2.json']
    for file in config_files:
        if not os.path.exists(os.path.join(config_base_path, file)):
            print(f"Error: Configuration file '{file}' not found in '{config_base_path}'.")
            return

    try:
        os.makedirs(install_path, exist_ok=True)
        os.makedirs(os.path.join(install_path, 'contexts'), exist_ok=True)
        for file in config_files:
            source = os.path.join(config_base_path, file)
            if 'contexts' in file:  # Check if the file is inside the 'contexts' directory
                destination = os.path.join(install_path, file)
            else:
                destination = install_path
            shutil.copy(source, destination)
    except Exception as e:
        print(f"Error copying configuration files: {e}")
        return

    try:
        with open(os.path.expanduser('~/.bashrc'), 'a') as f:
            f.write(f'\nexport NEUTRON_ROOT="{install_path}"\n')
        print("NEUTRON_ROOT has been saved in .bashrc")
    except Exception as e:
        print(f"Error adding environment variable to .bashrc: {e}")


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
