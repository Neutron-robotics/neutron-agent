# Neutron Agent

The Neutron Agent the software component that bridges your robotic system and the Neutron Robotics platform. It empowers you to seamlessly control and monitor your robots in real time, unlocking automation, data collection, and remote operation possibilities.

## Key Features

* **Seamless Communication:** Establishes a robust and secure communication channel between your robot and the Neutron server.
* **Process Management:** Efficiently manages processes running on your robotic system.
* **Job Execution and Command Handling:** Acts as a command center for your robot, receiving and executing commands from the Neutron server.
* **ROS Integration (Optional):** Seamlessly integrates with the Robot Operating System (ROS) if your robot utilizes it.
* **System Linking:** Simplifies linking your physical robot to its digital representation on the Neutron platform.
* **Status Reporting:** Continuously publishes status reports to the Neutron platform, providing insights into your robot's condition.
* **Real-Time Control:** Enables real-time control of your robot through the Neutron web interface.

## Installation

1. **Download the agent** 
```
git clone git@github.com:hugoperier/neutron-agent.git
```

2. **Installation:**
 ```
    cd neutron-agent
    python3 src/agent.py --install
 ```

You will be prompted for the location of the .neutron folder, containing configurations and script location

3. **Linking to Your Robot:**
 ```
    python3 src/agent.py --link
 ```

Enter the secret key that is available from the robot page in the neutron robotics platform.

## Usage

The Neutron Agent works in conjunction with the Neutron Robotics web interface, providing a comprehensive solution for robot control and monitoring. Refer to the Neutron Robotics documentation for detailed instructions on using the web interface and its features.

## Contributing

We welcome contributions to the Neutron Agent project! If you encounter issues, have feature requests, or want to contribute code, please open an issue or submit a pull request on our GitHub repository.

## License

This project is licensed under the GNU GENERAL PUBLIC License. See the LICENSE file for details.