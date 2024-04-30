
# Tableau BridgeCTL
BridgeCTL is a utility for Tableau Bridge Linux Containers.

[![Community Supported](https://img.shields.io/badge/Support%20Level-Community%20Supported-457387.svg)](https://www.tableau.com/support-levels-it-and-developer-tools)
[![GitHub](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://raw.githubusercontent.com/Tableau/TabPy/master/LICENSE)

### Introduction
BridgeCTL will help you build your Tableau Bridge Linux container images including downloading and 
installing the right database drivers and bridge .rpm installer. Then it will help you easily configure and 
run your bridge containers in Docker or Kubernetes with the correct bridge settings (Tableau sitename, pool, PAT Token, etc.). 
It will help you monitor the status and configuration of your running bridge agents and to also help analyze your bridge logs. 
BridgeCTL can be installed on Linux, Windows or Mac.

### Setup
BridgeCTL is easy to install. Just download and run the bridgectl_setup.py script using the following commands:

```
curl -OL https://github.com/tableau/bridgectl/releases/download/setup/bridgectl_setup.py
python bridgectl_setup.py
```

### 
Note python 3.10 or greater is required. Please use the appropriate python command on your machine to run the setup script, for example instead of "python" you may need to use "python3" or "python3.11". 
You can also install bridgectl in a python virtual environment.
The BridgeCTL setup script will create a folder "bridgectl" and unzip files into this folder. 
It will then install several pip libraries and then it will create a shortcut function so you can use the global command "bridgectl". 
Each time BridgeCTL starts, it will check for updates.

### Requirements
- Python >= 3.10
- For running Bridge on Linux containers: Docker Desktop
- BridgeCTL can be installed on Windows, Linux or Mac (as long as the correct version of Python is installed)

Optional Requirements
- If you would like to run bridge agents containers in Kubernetes you will need access to AWS ECR (Container Regisry) and a Kubernetes cluster. You will also need valid aws cli credentials to access the AWS ECR and a valid kubeconfig to access the k8s cluster.

### Features
- Build Tableau Bridge docker container images
  - This includes downloading the latest bridge rpm from tableau.com.
  - Download and install database drivers, we use the container_image_builder utility to allow the user to select a set of database drivers from a dropdown list.
  - Follow best practices for building containers
- Run bridge containers in Docker
  - User can easily select configuration settings from Tableau Cloud required to run bridge agents (pool_id, site_name, etc.)
  - Spin up bridge agent containers in Docker
- Reports
  - Display Jobs Report
  - Display Bridge Agent Status
- Analyze bridge logs
  - Log viewer with ability to filter and sort logs
  - Analyze logs from local docker containers, local disk or from kubernetes containers (pods)
- Run bridge containers in Kubernetes
  - After importing your kubeconfig file, you can spin up bridge agent containers in a Kubernetes cluster
- Manage bridge containers in Docker or Kubernetes
  - View configuration settings of bridge containers or delete bridge containers
  - View current bridge agent activity (standard output logs)
  - Show snapshot metrics about resource utilization

### Terms of Use
This repo contains utilities and source code example files for creating and running Tableau bridge Linux containers. These scripts may be useful but are unsupported. Please get help from other users on the Tableau Community Forums.

### Documentation for Tableau Bridge
See official Tableau documentation for creating bridge containers on Linux
https://help.tableau.com/current/online/en-us/to_bridge_linux_install.htm


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
