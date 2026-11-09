"use strict";

const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");
const test = require("node:test");

const { copyHelperBesideArtifacts } = require("./after_all_artifact_build");

test("Clear Quarantine.command is copied next to each artifact directory", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "osa-helper-"));
  const dmg = path.join(root, "Open Sustainability Analyst.dmg");
  fs.writeFileSync(dmg, "dmg");

  const extras = copyHelperBesideArtifacts([dmg]);
  const helper = path.join(root, "Clear Quarantine.command");

  assert.deepEqual(extras, [helper, path.join(root, "INSTALL-MAC.md")]);
  assert.equal(fs.statSync(helper).mode & 0o111, 0o111);
  assert.match(fs.readFileSync(helper, "utf8"), /xattr -cr/);
  assert.match(fs.readFileSync(path.join(root, "INSTALL-MAC.md"), "utf8"), /Clear Quarantine/);
});
