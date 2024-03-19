# Release notes

### Version 2.1.53 (Mar 20, 2024)
- Add a button to check for updates from Settings Page in the UI
- Add uninstall command to help menu
- Additional Kubernetes integration features
  
### Version 2.1.48 (Mar 19,2024)
- Add jobs detail checkbox which will include job luid and other details about the bridge job.
- Add feedback survey link to Home page.

### Version 2.1.41 (Mar 1, 2024)
- Add cli menu command to configure systemctl service startup on Linux
- Bugfix: fix error when no jobs in job report
 
### Version 2.1.20 (Feb 19, 2024)
- Add Kubernetes and AWS Elastic Container Registry (ECR) support

### Version 2.0.124
- Improve Windows support for BridgeCTL. Fix bug: duplicate PATH entries.
- Filewatcher prototype

### Version 2.0.19
- Auto-update BridgeCTL: Deployment of BridgeCTL via github releases

### Version 2.0.6
- Search Bridge logs

### Version 2.0.5
- Bug fixes on windows
- Bug fixes for Manage bridge containers
- Auth token editing

### Version 2.0.3
- Edit Bridge Settings from web UI: ability to edit the bridge settings
- Mockup of DC-PAT Web UI

### Version 2.0.1
- Add new Streamlit UI
- Rename to BridgeCTL
- add docker pip library for interacting with docker instead of using subprocess calls to docker commands, this reduces the amount of code, and improves cross-platform support.

### Version 1.2.157
- fix base dockerimage to point to Redhat a base image from dockerhub instead of artifactory.

### Version 1.2.20
- move setup script to DC WebApp instead of Artifactory.
- ability to specify specific the latest rpm for a branch for bridge RPMs, for example "tableau-2023-2.latest" 
- ability to specify a specific bridge rpm version, for example: "tableau-2022-4.23.0519.1315"

### Version 1.1.70
- Add beta menu - k8s cluster onboarding wizard for collecting customer info and returning a cluster.tar.

### Version 1.1.62
- Ability to call the Jobs API, and display in the Beta -> Show Jobs Report

### Version 1.1.59
- Switch bridge image to use environment variables instead of creating start-bridgeclient.sh and tokenFile.json outside the container. This will make the images more reusable.

### Version 1.1.30
- Enable BridgeCTL to work on Windows (still in beta)

### Version 1.1.29
- Improved manage bridge containers menu which includes these functions: 
  + Agent Logs Summary
  + Container info from DB
  + Docker logs
  + Kill container

### Version 1.1.17
- add commandline parameters  (--build, --run or --update) for automation scenarios. See [Documentation](https://salesforce.okta.com/app/salesforce_confluence_1/exk171qpzbBxPEXKI697/sso/saml)

### Version 1.1.7
- Tokens.yml includes a pod_url property which contains the tableau_cloud_serverpod_url so that other TC environments can be used. 
- Also, the pod_url in the tokens.yml is checked when running a container that the target site+pod_url matches from settings.yml.
- Containers DB (config/containers.yml) tracks which tokens are used per container so we ensure each token is only used once. Menu command added which displays database record information for Container

### Version 1.1.1
- Various improvements to edit settings on Linux
- fixes to download file

### Version 1.0.51
- default bridge rpm source set to github.com/tableau/bridge/releases/latest/download/tableau-bridge.rpm for easier first-time download (see the settings.yml bridge_rpm_source: which can be set to 'devbuilds' (internal daily builds) or 'github' (public beta releases)

### Version 1.0.50
- docker login to artifactory before build image to download base image

### Version 1.0.49
- store Tableau Cloud sitename in settings.yml (it will need to match the sitename from the token found in tokens.yml

### Version 1.0.48
- Improved Container management: ability to kill and report logs for stopped bridge containers

### Version 1.0.46
- In settings.yml, you can set the bridge.tableau_cloud_serverpod_url, and that will set in the container. 
TC Prod: https://prod-useast-a.online.tableau.com
executed in start-bridgeclient.sh: 
 /opt/tableau/tableau_bridge/bin/TabBridgeClientCmd setServiceConnection \
    --service="https://"

### Version 1.0.37
- define list of drivers in settings.yml
- download drivers and build into Docker image

### Version 1.0.21
- Build local bridge image with drivers
- Download rpm file from devbuilds web
- Manage local bridge containers (display commands to kill container or to view logs of container)

### Version 1.0.20
- Build local bridge image with RPM file
- Browse to Tableau Cloud Bridge Settings
- Edit settings in text editor
