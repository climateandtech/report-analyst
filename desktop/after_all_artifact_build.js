"use strict";

// Copy the one-click Gatekeeper helper next to the DMG/zip so testers do not
// need Terminal. Ad-hoc signing alone cannot clear the download quarantine.

const fs = require("fs");
const path = require("path");

const HELPER_NAME = "Clear Quarantine.command";
const INSTALL_NOTE = "INSTALL-MAC.md";

function copyBesideArtifacts(artifactPaths, relativeSource, fileName, mode) {
  const source = path.join(__dirname, relativeSource);
  if (!fs.existsSync(source)) {
    throw new Error(`missing ${source}`);
  }
  const contents = fs.readFileSync(source);
  const dirs = new Set(artifactPaths.map((artifact) => path.dirname(artifact)));
  const extras = [];
  for (const directory of dirs) {
    const target = path.join(directory, fileName);
    fs.writeFileSync(target, contents, { mode });
    if (mode) {
      fs.chmodSync(target, mode);
    }
    extras.push(target);
  }
  return extras;
}

function copyHelperBesideArtifacts(artifactPaths) {
  return [
    ...copyBesideArtifacts(artifactPaths, path.join("build", HELPER_NAME), HELPER_NAME, 0o755),
    ...copyBesideArtifacts(artifactPaths, INSTALL_NOTE, INSTALL_NOTE, 0o644),
  ];
}

exports.default = async function afterAllArtifactBuild(buildResult) {
  return copyHelperBesideArtifacts(buildResult.artifactPaths || []);
};

module.exports.copyHelperBesideArtifacts = copyHelperBesideArtifacts;