#!/bin/bash
set -o errexit; set -o nounset
echo "{\"$TOKEN_ID\":\"$TOKEN_VALUE\"}" > tokenFile.json
if [ -n "${UNC_PATH_MAPPINGS:-}" ]; then
  current_dir=$(pwd)
  echo "$UNC_PATH_MAPPINGS" > "$current_dir/tableau_bridge_unc_map.txt"
  export TABLEAU_BRIDGE_UNC_MAP_OVERRIDE="$current_dir/tableau_bridge_unc_map.txt"
  echo -e "tableau_bridge_unc_map.txt: $UNC_PATH_MAPPINGS"
fi
set -o xtrace

/opt/tableau/tableau_bridge/bin/TabBridgeClientCmd setServiceConnection --service="$TC_SERVER_URL"
/opt/tableau/tableau_bridge/bin/TabBridgeClientWorker -e \
   --client="${AGENT_NAME}" \
   --site="${SITE_NAME}" \
   --userEmail="${USER_EMAIL}" \
   --patTokenId="${TOKEN_ID}" \
   --patTokenFile=tokenFile.json \
   --poolId="${POOL_ID}"
