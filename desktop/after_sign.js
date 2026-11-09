"use strict";

// When there is no Developer ID, electron-builder may skip signing. Seal the
// outer .app with an ad-hoc signature and entitlements that allow Electron
// Framework (different Team ID) to load. Never use --deep here.

const path = require("path");

const { ADHOC_IDENTITY, developerIdIdentity, signAppBundle } = require("./sign_python");

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
  signAppBundle(appPath, ADHOC_IDENTITY, entitlements);
}

exports.default = afterSign;
module.exports = afterSign;
