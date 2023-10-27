
### Scripts for creating Tableau Bridge on Linux Docker Container, and for running/stopping bridge containers.

## Disclaimer
This repo contains source code and example files for creating Tableau bridge Linux containers. 
These scripts may be useful but are unsupported. Get help from other users on the Tableau Community Forums.

## High-Level Steps
1. Collect the required information including tableau cloud site_name, pool_id, PAT token id and secret, etc. Enter this into a yaml file. 
2. Create a Tableau Bridge Linux container
3. Run the Tableau Bridge Linux container

## Prerequisites
1. Docker
2. Bash shell (On Mac and Linux it is included and on Windows, you can install Windows Subsystem for Linux)
3. For Database Drivers, you'll need a bash script to download and install them in the container.


