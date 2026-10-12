#!/bin/sh
set -e

echo "LAN agent sandbox starting"
echo "  ingest=${INGEST_PATH:-/ingest}"
echo "  workspace=${WORKSPACE_PATH:-/workspace}"
echo "  profile=${AGENT_PROFILE:-document-chatbot}"

mkdir -p "${WORKSPACE_PATH:-/workspace}/scripts"

exec lan-agent
