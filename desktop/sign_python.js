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

function signOne(identity, entitlements, target) {
  execFileSync("/usr/bin/codesign", codesignArgs(identity, entitlements, target), { stdio: "inherit" });
}

function signAppBundle(appPath, identity, entitlements) {
  // Do not use --deep. Sign helpers and frameworks inside-out so each process
  // gets disable-library-validation; otherwise dyld rejects Electron Framework
  // for "different Team IDs" under hardened runtime.
  const frameworks = path.join(appPath, "Contents", "Frameworks");
  const electronFramework = path.join(frameworks, "Electron Framework.framework");
  const crashpad = path.join(
    electronFramework,
    "Versions",
    "A",
    "Helpers",
    "chrome_crashpad_handler",
  );
  if (fs.existsSync(crashpad)) {
    signOne(identity, entitlements, crashpad);
  }
  if (fs.existsSync(path.join(electronFramework, "Versions", "A", "Electron Framework"))) {
    signOne(identity, entitlements, path.join(electronFramework, "Versions", "A", "Electron Framework"));
  }
  if (fs.existsSync(electronFramework)) {
    signOne(identity, entitlements, electronFramework);
  }
  for (const name of ["Mantle", "ReactiveObjC", "Squirrel"]) {
    const framework = path.join(frameworks, `${name}.framework`);
    if (fs.existsSync(framework)) {
      signOne(identity, entitlements, framework);
    }
  }
  if (fs.existsSync(frameworks)) {
    for (const entry of fs.readdirSync(frameworks)) {
      if (!entry.endsWith(".app")) {
        continue;
      }
      signOne(identity, entitlements, path.join(frameworks, entry));
    }
  }
  signOne(identity, entitlements, appPath);
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
    // electron-builder skips afterSign when it finds no identity.
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
