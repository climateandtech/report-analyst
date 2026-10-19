"use strict";

// Sign Mach-O files inside the bundled CPython prefix before electron-builder
// signs the app. Without a Developer ID this is a no-op so local packs still run.

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const MACH_O_MAGICS = new Set([
  0xfeedface, 0xcefaedfe, 0xfeedfacf, 0xcffaedfe, 0xcafebabe, 0xbebafeca,
]);

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

function signingIdentity() {
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

function signPrefix(prefix, identity, entitlements) {
  for (const file of machOPaths(prefix)) {
    execFileSync(
      "/usr/bin/codesign",
      ["--force", "--sign", identity, "--options", "runtime", "--timestamp", "--entitlements", entitlements, file],
      { stdio: "inherit" },
    );
  }
}

function isMasTarget(context) {
  return (context.targets || []).some((target) => target.name === "mas" || target.name === "mas-dev");
}

async function afterPack(context) {
  if (context.electronPlatformName !== "darwin" || isMasTarget(context)) {
    return;
  }
  const identity = signingIdentity();
  if (!identity) {
    console.log("skipped Python prefix signing: no Developer ID Application identity");
    return;
  }
  const appName = context.packager.appInfo.productFilename;
  const prefix = path.join(context.appOutDir, `${appName}.app`, "Contents", "Resources", "python");
  signPrefix(prefix, identity, path.join(__dirname, "build", "entitlements.mac.plist"));
}

module.exports = afterPack;
module.exports.isMachO = isMachO;
module.exports.machOPaths = machOPaths;
module.exports.signPrefix = signPrefix;
module.exports.signingIdentity = signingIdentity;
