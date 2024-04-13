# Release notes

 
### Version 2.1.108 (April 10, 2024)
- BridgeCTL now supports building bridge images on Arm processors even though tableau bridge rpm uses x86.
- On run bridge container, there is now an option to show a complete bash script which can be copied/pasted to a remove machine to run a bridge agent without having to install bridgectl on that remote machine. (This requires pushing the built image to ECR)

### Version 2.1.98 (April 6, 2024)
- Add support for downloading latest Tableau Bridge RPM from tableau.com
- Fix log paths for release version of bridge

### Version 2.1.93 (April 3, 2024)
- Added support for adding bridge agents to the Default Pool
- Additional validation improvements when running bridge agents.
- Improved instructions for Settings - Bulk import PAT tokens.

### Version 2.1.90 (April 2, 2024)
- Improved validation when adding PAT tokens, make sure it has the right permissions (SiteAdministrator).

### Version 2.1.88 (March 31, 2024)
- Improve instructions for building and running bridge containers, and error messages for connecting to ECR.

### Version 2.1.72 (Mar 28, 2024)
- Improvements to bridgectl_setup script
- Example bash scripts for running bridge on linux from the terminal
- Switch from Public ECR to private ECR support

### Version 2.1.61 (Mar 23, 2024)
- Settings page - Bulk Import PAT Token YAML
- Fixes and improvements for Private ECR support
- Improvements to running bridge containers in K8s

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

### Version 2.0.124 (Jan 8, 2024)
- Improve Windows support for BridgeCTL. Fix bug: duplicate PATH entries.
- Filewatcher prototype
- Auto-update BridgeCTL: Deployment of BridgeCTL via github releases

### Version 2.0.6 (Dec 13, 2023)
- Search Bridge logs
- Bug fixes on windows
- Bug fixes for Manage bridge containers
- Auth token editing
- Edit Bridge Settings from web UI: ability to edit the bridge settings
- Mockup of DC-PAT Web UI

### Version 2.0.1 (Nov 28, 2023)
- Add new Streamlit UI
- Rename to BridgeCTL
- add docker pip library for interacting with docker instead of using subprocess calls to docker commands, this reduces the amount of code, and improves cross-platform support.

### Version 1.2.157 (Aug 30, 2023)
- fix base dockerimage to point to Redhat a base image from dockerhub instead of artifactory.
- move setup script to DC WebApp instead of Artifactory.
- ability to specify specific the latest rpm for a branch for bridge RPMs, for example "tableau-2023-2.latest" 
- ability to specify a specific bridge rpm version, for example: "tableau-2022-4.23.0519.1315"

### Version 1.1.70
- Add beta menu - k8s cluster onboarding wizard for collecting customer info and returning a cluster.tar.
- Ability to call the Jobs API, and display in the Beta -> Show Jobs Report
- Switch bridge image to use environment variables instead of creating start-bridgeclient.sh and tokenFile.json outside the container. This will make the images more reusable.
- Enable BridgeCTL to work on Windows (still in beta)

### Version 1.1.29
- Improved manage bridge containers menu which includes these functions: 
  + Agent Logs Summary
  + Container info from DB
  + Docker logs
  + Kill container
- add commandline parameters  (--build, --run or --update) for automation scenarios. See [Documentation](https://salesforce.okta.com/app/salesforce_confluence_1/exk171qpzbBxPEXKI697/sso/saml)

### Version 1.1.7
- Tokens.yml includes a pod_url property which contains the tableau_cloud_serverpod_url so that other TC environments can be used. 
- Also, the pod_url in the tokens.yml is checked when running a container that the target site+pod_url matches from settings.yml.
- Containers DB (config/containers.yml) tracks which tokens are used per container so we ensure each token is only used once. Menu command added which displays database record information for Container
- Various improvements to edit settings on Linux
- fixes to download file

### Version 1.0.51
- default bridge rpm source set to github.com/tableau/bridge/releases/latest/download/tableau-bridge.rpm for easier first-time download (see the settings.yml bridge_rpm_source: which can be set to 'devbuilds' (internal daily builds) or 'github' (public beta releases)
- docker login to artifactory before build image to download base image
- store Tableau Cloud sitename in settings.yml (it will need to match the sitename from the token found in tokens.yml
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
- Build local bridge image with drivers
- Download rpm file from devbuilds web
- Manage local bridge containers (display commands to kill container or to view logs of container)

### Version 1.0.20 (June 10, 2023)
- Build local bridge image with RPM file
- Browse to Tableau Cloud Bridge Settings
- Edit settings in text editor


### Version 2.1.next (April __, 2024)
- Addition of the `--push_image`command-line parameter to push the last locally built container image to AWS ECR Container Registry.
- Add support for Minerva Bridge RPM. (Minerva is the new bridge query engine which will be released sometime later this year.)
- Add check that when running on Windows, the docker OsType is correctly set to linux, not windows

