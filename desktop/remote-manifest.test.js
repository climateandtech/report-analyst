"use strict";

const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");
const test = require("node:test");

const remote = require("./remote-manifest");

const NOW = new Date("2026-10-19T12:00:00Z");

function releaseJson(fields) {
  return JSON.stringify({
    version: "0.9.0",
    minVersion: "0.8.0",
    url: "https://github.com/climateandtech/report-analyst/releases",
    ...fields,
  });
}

test("a version below the minimum is a forced update", () => {
  const decision = remote.releaseDecision("0.7.0", remote.parseRelease(releaseJson({})));
  assert.equal(decision.block, true);
  assert.equal(decision.offer, false);
  assert.match(decision.message, /0\.7\.0/);
  assert.match(decision.message, /0\.8\.0/);
});

test("a supported but older version is a dismissible update", () => {
  const decision = remote.releaseDecision("0.8.0", remote.parseRelease(releaseJson({})));
  assert.equal(decision.block, false);
  assert.equal(decision.offer, true);
  assert.equal(decision.version, "0.9.0");
});

test("the current version neither blocks nor offers", () => {
  const decision = remote.releaseDecision(
    "0.9.0",
    remote.parseRelease(releaseJson({ version: "0.9.0", minVersion: "0.9.0" })),
  );
  assert.equal(decision.block, false);
  assert.equal(decision.offer, false);
});

test("a broken release file does not block the app", () => {
  const decision = remote.releaseDecision("0.8.0", remote.parseRelease("not-json"));
  assert.equal(decision.block, false);
  assert.equal(decision.url, null);
});

test("a non-https download link is dropped", () => {
  const decision = remote.releaseDecision(
    "0.7.0",
    remote.parseRelease(releaseJson({ url: "http://example.com/app.zip" })),
  );
  assert.equal(decision.block, true);
  assert.equal(decision.url, null);
});

test("dismissing an offered version hides that version only", () => {
  const older = remote.releaseDecision("0.8.0", remote.parseRelease(releaseJson({})));
  const state = remote.withDismissedUpdate(remote.loadState(""), older.version);
  assert.equal(remote.shouldOfferUpdate(older, state), false);
  const newer = remote.releaseDecision(
    "0.8.0",
    remote.parseRelease(releaseJson({ version: "0.10.0" })),
  );
  assert.equal(remote.shouldOfferUpdate(newer, state), true);
});

test("notices stay inside their dates and are plain text", () => {
  const text = JSON.stringify({
    notices: [
      { id: "live", message: "A note from us.", url: "https://example.com/note" },
      { id: "later", message: "Not yet.", startsAt: "2026-11-01" },
      { id: "old", message: "Finished.", endsAt: "2026-10-01" },
      { id: "markup", message: "<b>no</b>" },
      { id: "bad-link", message: "Nope.", url: "javascript:alert(1)" },
      { id: "Bad Id", message: "Nope." },
    ],
  });
  const active = remote.activeNotices(remote.parseNotices(text), NOW, []);
  assert.deepEqual(
    active.map((notice) => notice.id),
    ["live"],
  );
  assert.equal(active[0].url, "https://example.com/note");
});

test("a dismissed notice is not shown again", () => {
  const notices = remote.parseNotices(
    JSON.stringify({ notices: [{ id: "live", message: "Hello." }] }),
  );
  const state = remote.withDismissedNotice(remote.loadState("{"), "live");
  assert.deepEqual(remote.activeNotices(notices, NOW, state.dismissedNotices), []);
});

test("corrupt dismissal state is ignored", () => {
  assert.deepEqual(remote.loadState("{"), { dismissedNotices: [], dismissedUpdate: null });
});

test("manifest fetches stay on the jsDelivr host", async () => {
  await assert.rejects(
    remote.fetchText("https://raw.githubusercontent.com/climateandtech/report-analyst/main/x"),
    /not allowed/,
  );
  let called = false;
  await assert.rejects(
    remote.fetchText("http://cdn.jsdelivr.net/gh/x", () => {
      called = true;
      return Promise.resolve("{}");
    }),
    /not allowed/,
  );
  assert.equal(called, false);
});

test("the dismissal file is stored beside the analysis data", () => {
  const home = path.join(os.tmpdir(), "osa-home");
  const file = remote.statePath("darwin", {}, home);
  assert.equal(
    file,
    path.join(home, "Library", "Application Support", "Open Sustainability Analyst", "remote-state.json"),
  );
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "osa-state-"));
  const stateFile = path.join(directory, "remote-state.json");
  remote.saveState(stateFile, remote.withDismissedNotice(remote.loadState(""), "live"));
  assert.deepEqual(remote.readState(stateFile).dismissedNotices, ["live"]);
});
