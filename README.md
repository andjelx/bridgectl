
# Tableau BridgeCTL
BridgeCTL is a utility to run, monitor, and troubleshoot Tableau Bridge agents. 

### Introduction
BridgeCTL will help you build your Tableau Bridge Linux container images including downloading and installing the right database drivers and bridge installer version. Then it will help you easily configure and run your bridge containers with the correct bridge settings (Tableau sitename, pool, PAT Token, etc.). And finally it will help you monitor the status and configuration of your running bridge agents, and to analyze your bridge agents logs. Also, it can deploy bridge containers to Docker or Kubernetes.
Note that BridgeCTL runs on Linux, Windows or Mac. 

### Setup
BridgeCTL is easy to install. Just download and run the bridgectl_setup.py script using the following commands:

**Mac and Linux**
```
curl -L https://github.com/tableau/bridgectl/releases/download/setup/bridgectl_setup.py --output bridgectl_setup.py
python bridgectl_setup.py
```

**Windows**
```
curl https://github.com/tableau/bridgectl/releases/download/setup/bridgectl_setup.py -O bridgectl_setup.py
python bridgectl_setup.py
```

### 
Note python 3.10 or greater is required. Please use the appropriate python command to run the setup script, for example instead of "python" you may need to use "python3" or "python3.11".
The BridgeCTL setup script will create a folder "bridgectl" and unzip files into this folder. It will also create a shortcut function so you can use the command "bridgectl". Each time BridgeCTL starts, it will check for updates.

### Requirements
- Python >= 3.10
- For running Bridge on Linux containers: Docker Desktop
- BridgeCTL can be installed on Windows, Linux or Mac (as long as python3 is installed)

#### Demo
[Getting started with BridgeCTL](https://www.youtube.com/watch?v=n_jMKC9t6hw)

### Features
- Build Tableau Bridge docker container images
  - This includes downloading the latest bridge rpm from tableau.com.
  - Download and install database drivers, we use the container_image_builder utility to allow the user to select a set of database drivers from a dropdown list.
  - Follow best practices for building containers
- Run bridge containers in Docker
  - User can easily select configuration settings from Tableau Cloud required to run bridge agents (pool_id, site_name, etc.)
  - Spin up bridge agent containers in Docker
- Manage bridge containers in Kubernetes
  - Spin up bridge agent containers in Kubernetes
- Reports
  - Display Jobs Report
  - Display Bridge Agent Status
- Analyze bridge logs
  - Log viewer with ability to filter and sort logs
  - Analyze logs from local disk, local docker containers, or from kubernetes
- Manage bridge containers in Docker or Kubernetes
  - View configuration settings and resource utilization of bridge containers
  - Delete a bridge container
  - View current bridge agent activity (standard output logs)
  - Show metrics about resource utilization

### Terms of Use
This repo contains utilities and source code example files for creating and running Tableau bridge Linux containers. These scripts may be useful but are unsupported. Please get help from other users on the Tableau Community Forums.

### Documentation for Tableau Bridge
See official Tableau documentation for creating bridge containers on Linux
https://help.tableau.com/current/online/en-us/to_bridge_linux_install.htm

### Example scripts
For example bash scripts for creating Bridge on Docker see the sub folder: /example_build_docker_basic

### Release Notes
[Release Notes](RELEASE_NOTES.md)

<br><br><br>
### User interface screenshots
Home
![BridgeCTL Home](assets/home2.png)

Analyze Logs
![BridgeCTL Logs](assets/logs.png)

Command-line Interface

![BridgeCTL CLI](assets/cli.png)
