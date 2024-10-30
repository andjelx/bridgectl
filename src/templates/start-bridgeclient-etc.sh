#!/bin/bash

set -o errexit; set -o xtrace; set -o nounset

/opt/tableau/tableau_bridge/bin/TabBridgeClientCmd setServiceConnection --service="$TC_SERVER_URL"
#/opt/tableau/tableau_bridge/bin/TabBridgeClientCmd setConfiguration --JSONLogForExtractRefresh=true
#LC_ALL=en_US.UTF-8 /opt/tableau/tableau_bridge/bin/TabBridgeClientCmd

/opt/tableau/tableau_bridge/bin/TabBridgeClientWorker -e --client="${AGENT_NAME}" \
   --site="${SITE_NAME}" \
   --userEmail="${USER_EMAIL}" \
   --patTokenId="${TOKEN_ID}" \
   --patTokenFile=/etc/tokenFile.json \
   --poolId="${POOL_ID}"
