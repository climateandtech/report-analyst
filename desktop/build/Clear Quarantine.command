#!/bin/bash
# Clears the macOS download quarantine so an unsigned build can open.
# Drag Open Sustainability Analyst to Applications first, then double-click this file.

set -euo pipefail

APP_NAME="Open Sustainability Analyst.app"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

candidates=(
  "/Applications/${APP_NAME}"
  "${SCRIPT_DIR}/${APP_NAME}"
  "${HOME}/Applications/${APP_NAME}"
)

APP=""
for path in "${candidates[@]}"; do
  if [[ -d "${path}" ]]; then
    APP="${path}"
    break
  fi
done

if [[ -z "${APP}" ]]; then
  osascript <<'EOF'
display dialog "Move “Open Sustainability Analyst” into Applications, then run Clear Quarantine again." buttons {"OK"} default button 1 with title "Open Sustainability Analyst"
EOF
  exit 1
fi

xattr -cr "${APP}"
open "${APP}"

osascript <<EOF
display dialog "Quarantine cleared for:
${APP}

The app should open now. You only need to do this once after each download." buttons {"OK"} default button 1 with title "Open Sustainability Analyst"
EOF
