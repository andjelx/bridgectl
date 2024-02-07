
# Tableau BridgeCTL
BridgeCTL is a utility to run, monitor, and troubleshoot Tableau Bridge agents. BridgeCTL runs on Linux, Windows or Mac.

### Setup
BridgeCTL is easy to install. Just download and run the bridgectl_setup.py script using the following commands:
```
curl -L https://github.com/tableau/bridgectl/releases/download/setup/bridgectl_setup.py --output bridgectl_setup.py
python bridgectl_setup.py
```
Note python 3.10 or greater is required. Please use the appropriate python command to run the setup script, for example instead of "python" you may need to use "python3" or "python3.11".
The BridgeCTL setup script will create a folder "bridgectl" and unzip files into this folder. It will also create a shortcut function so you can use the command "bridgectl".

### Requirements
- Python >= 3.10
- For running Bridge on Linux containers: Docker Desktop
- BridgeCTL can be installed on Windows, Linux or Mac (as long as python3 is installed)

#### Automatic updates
Each time BridgeCTL starts, it will check for updates.

### Features
- Build Tableau Bridge docker container images
  - This includes downloading the latest bridge rpm from tableau.com.
  - Download and install database drivers, we use the container_image_builder utility to allow the user to select a set of database drivers from a dropdown list.
  - Follow best practices for building containers
- Run bridge containers
  - User can easily select configuration settings from Tableau Cloud required to run bridge agents (pool_id, site_name, etc.)
  - Spin up bridge agent containers in Docker
  - Spin up bridge agent containers in Kubernetes
- Analyze bridge logs
  - Log viewer with ability to filter and sort logs
  - Analyze logs from local disk, local docker containers, or from kubernetes
- Manage bridge containers
  - View configuration settings and resource utilization for local bridge containers in docker
  - Delete a bridge container
  - View current bridge agent activity 
  - Show summary metrics about the Bridge logs
- Reports
  - Display Jobs Report
  - Display Bridge agent status
- Beta Features
  - Summarize logs using the GPT API, which makes it easier to identify and fix errors, and get a summary of activity on the agent.

### Documentation for Tableau Bridge
See official Tableau documentation for creating bridge containers on Linux
https://help.tableau.com/current/online/en-us/to_bridge_linux_install.htm

### Example scripts
For example bash scripts for creating Bridge on Docker see the sub folder: /example_build_docker_basic

### Terms of Use
This repo contains utilities, source code example files for creating Tableau bridge Linux containers.
These scripts may be useful but are unsupported. Please get help from other users on the Tableau Community Forums.

<br><br><br>
### User interface screenshots
Home
![BridgeCTL Home](assets/home2.png)

Analyze Logs
![BridgeCTL Logs](assets/logs.png)

Command-line Interface

![BridgeCTL CLI](assets/cli.png)
