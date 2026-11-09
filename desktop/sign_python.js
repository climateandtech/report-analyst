"use strict";

// Sign Mach-O files inside the bundled CPython prefix before electron-builder
// signs the app. Uses a Developer ID when one is available; otherwise ad-hoc ("-").

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const MACH_O_MAGICS = new Set([
  0xfeedface, 0xcefaedfe, 0xfeedfacf, 0xcffaedfe, 0xcafebabe, 0xbebafeca,
]);
const ADHOC_IDENTITY = "-";

function isMachO(buffer) {
  if (!Buffer.isBuffer(buffer) || buffer.length < 4) {
    return false;
  }
  return MACH_O_MAGICS.has(buffer.readUInt32BE(0)) || MACH_O_MAGICS.has(buffer.readUInt32LE(0));
}

function machOPaths(root) {
  const found = [];
  const walk = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) {
        continue;
      }
      if (entry.isDirectory()) {
        walk(fullPath);
        continue;
      }
      if (!entry.isFile()) {
        continue;
      }
      const handle = fs.openSync(fullPath, "r");
      try {
        const header = Buffer.alloc(4);
        fs.readSync(handle, header, 0, 4, 0);
        if (isMachO(header)) {
          found.push(fullPath);
        }
      } finally {
        fs.closeSync(handle);
      }
    }
  };
  if (fs.existsSync(root)) {
    walk(root);
  }
  return found.sort((left, right) => right.split(path.sep).length - left.split(path.sep).length);
}

function developerIdIdentity() {
  if (process.env.CSC_NAME) {
    return process.env.CSC_NAME;
  }
  try {
    const listing = execFileSync("/usr/bin/security", ["find-identity", "-v", "-p", "codesigning"], {
      encoding: "utf8",
    });
    const match = listing.match(/"((?:Developer ID Application|3rd Party Mac Developer Application): [^"]+)"/);
    return match ? match[1] : null;
  } catch (_error) {
    return null;
  }
}

function signingIdentity() {
  return developerIdIdentity() || ADHOC_IDENTITY;
}

function codesignArgs(identity, entitlements, file) {
  const args = ["--force", "--sign", identity, "--options", "runtime", "--entitlements", entitlements];
  if (identity !== ADHOC_IDENTITY) {
    args.push("--timestamp");
  }
  args.push(file);
  return args;
}

function signPrefix(prefix, identity, entitlements) {
  for (const file of machOPaths(prefix)) {
    execFileSync("/usr/bin/codesign", codesignArgs(identity, entitlements, file), { stdio: "inherit" });
  }
}

function isMasTarget(context) {
  return (context.targets || []).some((target) => target.name === "mas" || target.name === "mas-dev");
}

function signAppBundle(appPath, identity, entitlements) {
  const args = ["--force", "--sign", identity, "--options", "runtime", "--entitlements", entitlements];
  if (identity === ADHOC_IDENTITY) {
    // Seal nested Mach-O when electron-builder skips signing (no Developer ID).
    args.splice(1, 0, "--deep");
  } else {
    args.push("--timestamp");
  }
  args.push(appPath);
  execFileSync("/usr/bin/codesign", args, { stdio: "inherit" });
}

async function afterPack(context) {
  if (context.electronPlatformName !== "darwin" || isMasTarget(context)) {
    return;
  }
  const identity = signingIdentity();
  const appName = context.packager.appInfo.productFilename;
  const appPath = path.join(context.appOutDir, `${appName}.app`);
  const entitlements = path.join(__dirname, "build", "entitlements.mac.plist");
  const prefix = path.join(appPath, "Contents", "Resources", "python");
  if (identity === ADHOC_IDENTITY) {
    console.log("signing Python prefix with ad-hoc identity (no Developer ID on this machine)");
  }
  signPrefix(prefix, identity, entitlements);
  if (identity === ADHOC_IDENTITY) {
    // electron-builder's afterSign hook is skipped when it finds no identity.
    console.log(`ad-hoc sealing app bundle after pack: ${appPath}`);
    signAppBundle(appPath, identity, entitlements);
  }
}

module.exports = afterPack;
module.exports.isMachO = isMachO;
module.exports.machOPaths = machOPaths;
module.exports.signPrefix = signPrefix;
module.exports.signAppBundle = signAppBundle;
module.exports.signingIdentity = signingIdentity;
module.exports.developerIdIdentity = developerIdIdentity;
module.exports.codesignArgs = codesignArgs;
module.exports.ADHOC_IDENTITY = ADHOC_IDENTITY;
