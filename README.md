
# Tableau BridgeCTL
A command-line utility to build, run and monitor your Tableau Bridge Agents in Containers.

[![Community Supported](https://img.shields.io/badge/Support%20Level-Community%20Supported-457387.svg)](https://www.tableau.com/support-levels-it-and-developer-tools)
[![GitHub](https://img.shields.io/badge/license-AP2-brightgreen.svg)](https://github.com/tableau/bridgectl/blob/main/LICENSE.txt)

### Introduction
BridgeCTL will help you build your Tableau Bridge Linux container images including downloading and 
installing the right database drivers and bridge rpm installer. Then it will help you easily configure and 
run your bridge containers in Docker or Kubernetes with the correct connection settings. It has a convenient 
log viewer for bridge container logs in docker, kubernetes. It will also monitor the status and configuration of your 
running bridge agents and can send you an alert if one of your agents becomes disconnected. 
BridgeCTL can be installed on Linux, Windows or Mac.

### Setup
BridgeCTL is easy to install. Just download and run the bridgectl_setup.py script using the following two commands:

```
curl -OL https://github.com/tableau/bridgectl/releases/download/setup/bridgectl_setup.py
python bridgectl_setup.py
```

Requirements
- Python >= 3.10
- Docker Desktop
- BridgeCTL works on Windows, Linux or Mac

Note python 3.10 or greater is required. Please use the appropriate python command on your machine to run the setup script, for example instead of "python" you may need to use "python3" or "python3.11". 
The BridgeCTL setup script will create a folder "bridgectl" in the current directory and a python virtual environment named "tabenv". It will then create a shortcut function `bridgectl` so that you can conveniently use that global command from the terminal.

[Detailed Installation Instructions](../../wiki/Installation)

Optional Requirement:  If you would like to run bridge agents containers in Kubernetes you will need access to AWS Elastic Container Registry and a Kubernetes cluster.

### Quickstart Demo Video
![Home](assets/bridgectl_quickstart2.gif)


### Features
- Build Tableau Bridge docker container images
  - Download and install the bridge rpm and selected database drivers in the image.
  - Follow best practices for building containers.
- Run bridge containers in Docker
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


### Supportability & Help
BridgeCTL is provided as Community-Supported as defined [here](https://www.tableau.com/support/itsupport). BridgeCTL has a great deal of helpful documentaion in this wiki. There are also knowledgeable people in the Tableau Community Forums. In addition, questions can be posted in the Tableau #DataDev Slack workspace in #general channel.

### Documentation for Tableau Bridge
See [official Tableau documentation](https://help.tableau.com/current/online/en-us/to_bridge_linux_install.htm) for creating bridge containers on Linux


### Release Notes
[Release Notes](../../wiki/Release_Notes)

<br><br><br>
### User interface screenshots
Home

![Home](assets/home4.png)

Command-line Interface

![CLI](assets/cli2.png)__

Build Bridge Container Images
![Build](assets/build.png)

Analyze Logs
![BridgeCTL Logs](assets/logs.png)

Monitor Bridge Agent Health
![Monitor Bridge](assets/monitor_screenshot2.png)

Autoscale Bridge Pods in Kubernetes
![Monitor Bridge](assets/autoscale.png)

Example Dockerfile Scripts
![Example Scripts](assets/examples3.png)
