import os
import shutil

def create_install_path():
    install_path = input("Enter folder installation path (~/.neutron):").strip()
    if not install_path:
        install_path = os.path.expanduser("~/.neutron")

    # Check if the install path already exists
    if os.path.exists(install_path):
        response = input(f"The installation path '{install_path}' already exists. Do you want to continue? (y/n): ").strip().lower()
        if response != 'y':
            raise Exception(f"Installation aborted")
    return install_path

def copy_configuration(install_path):
    config_base_path = './configuration/'
    config_files = ['neutron.json', 'contexts/ros2.json', 'setup.sh']
    for file in config_files:
        if not os.path.exists(os.path.join(config_base_path, file)):
            raise Exception(f"Error: Configuration file '{file}' not found in '{config_base_path}'.")
    
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
        raise Exception(f"Error copying configuration files: {e}")
        return

def update_bashrc(install_path):
    bashrc_path = os.path.expanduser('~/.bashrc')
    try:
        with open(bashrc_path, 'r') as f:
            lines = f.readlines()
        lines = [line for line in lines if 'export NEUTRON_ROOT=' not in line]
        lines.append(f'\nexport NEUTRON_ROOT="{install_path}"\n')
        with open(bashrc_path, 'w') as f:
            f.writelines(lines)
        
        print("NEUTRON_ROOT has been updated in .bashrc")
    except Exception as e:
        raise Exception(f"Error updating .bashrc: {e}")

def add_neutron_alias(repo_path):
    bashrc_path = os.path.expanduser('~/.bashrc')
    alias_command = f'alias neutron-agent="python3 {repo_path}/agent.py"'
    
    try:
        with open(bashrc_path, 'r') as f:
            lines = f.readlines()

        lines = [line for line in lines if not line.startswith('alias neutron-agent=')]
        lines.append(f'\n{alias_command}\n')
        with open(bashrc_path, 'w') as f:
            f.writelines(lines)

    except Exception as e:
        print(f"Error updating .bashrc: {e}")