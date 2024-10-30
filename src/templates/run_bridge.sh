#!/bin/bash
set -ex
function aws_login(){
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
}
function run_container() {
  BRIDGE_IMAGE_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${AWS_ECR_IMAGE_REPO}:${BRIDGE_IMAGE_TAG}"
  BRIDGE_AGENT_NAME="bridge-${TOKEN_ID}"
  docker run -d --restart=on-failure:1 \
    --name $BRIDGE_AGENT_NAME \
    -e AGENT_NAME=$BRIDGE_AGENT_NAME \
    -e TC_SERVER_URL=$TC_SERVER_URL \
    -e SITE_NAME=$SITE_NAME \
    -e USER_EMAIL=$USER_EMAIL \
    -e POOL_ID=$POOL_ID \
    -e TOKEN_ID=$TOKEN_ID \
    -e TOKEN_VALUE=$TOKEN_VALUE \
    $BRIDGE_IMAGE_URL
}