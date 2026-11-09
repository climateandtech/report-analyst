"use strict";

// When there is no Developer ID, electron-builder may skip signing. Seal the
// whole .app with an ad-hoc signature so nested Python binaries match.

const { execFileSync } = require("child_process");
const path = require("path");

const { ADHOC_IDENTITY, developerIdIdentity } = require("./sign_python");

function isMasTarget(context) {
  return (context.targets || []).some((target) => target.name === "mas" || target.name === "mas-dev");
}

async function afterSign(context) {
  if (context.electronPlatformName !== "darwin" || isMasTarget(context)) {
    return;
  }
  if (developerIdIdentity()) {
    return;
  }
  const appName = context.packager.appInfo.productFilename;
  const appPath = path.join(context.appOutDir, `${appName}.app`);
  const entitlements = path.join(__dirname, "build", "entitlements.mac.plist");
  console.log(`ad-hoc signing app bundle: ${appPath}`);
  execFileSync(
    "/usr/bin/codesign",
    ["--force", "--deep", "--sign", ADHOC_IDENTITY, "--options", "runtime", "--entitlements", entitlements, appPath],
    { stdio: "inherit" },
  );
}

exports.default = afterSign;
module.exports = afterSign;
