"use strict";

// Release and notice files live in git and are fetched from jsDelivr.
// Edit desktop/remote/release.json and desktop/remote/notices.json, then push.
// The repo must be public: jsDelivr cannot read a private GitHub repo.

const fs = require("fs");
const https = require("https");
const os = require("os");
const path = require("path");

const APP_DATA_DIR_NAME = "Open Sustainability Analyst";
const RELEASE_URL =
  "https://cdn.jsdelivr.net/gh/climateandtech/report-analyst@desktop-poc/desktop/remote/release.json";
const NOTICES_URL =
  "https://cdn.jsdelivr.net/gh/climateandtech/report-analyst@desktop-poc/desktop/remote/notices.json";
const MAX_BYTES = 65536;
const MAX_NOTICES = 3;
const VERSION_RE = /^\d+\.\d+\.\d+$/;
const NOTICE_ID_RE = /^[a-z0-9][a-z0-9-]{0,63}$/;

function isVersion(value) {
  return typeof value === "string" && VERSION_RE.test(value);
}

function compareVersions(left, right) {
  const a = left.split(".").map(Number);
  const b = right.split(".").map(Number);
  for (let index = 0; index < 3; index += 1) {
    if (a[index] !== b[index]) {
      return a[index] < b[index] ? -1 : 1;
    }
  }
  return 0;
}

function isHttpsUrl(value) {
  if (typeof value !== "string" || value.length > 500) {
    return false;
  }
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.username === "" && url.password === "";
  } catch (_error) {
    return false;
  }
}

function assertAllowedManifestUrl(value) {
  const url = new URL(value);
  if (url.protocol !== "https:" || url.hostname !== "cdn.jsdelivr.net") {
    throw new Error("remote manifest host is not allowed");
  }
  if (url.username || url.password) {
    throw new Error("remote manifest host is not allowed");
  }
}

function parseRelease(text) {
  if (typeof text !== "string") {
    return null;
  }
  let data;
  try {
    data = JSON.parse(text);
  } catch (_error) {
    return null;
  }
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return null;
  }
  return {
    version: isVersion(data.version) ? data.version : null,
    minVersion: isVersion(data.minVersion) ? data.minVersion : null,
    url: isHttpsUrl(data.url) ? data.url : null,
  };
}

function releaseDecision(current, release) {
  const idle = { block: false, offer: false, version: null, url: null, message: "" };
  if (!isVersion(current) || !release) {
    return idle;
  }
  const url = release.url;
  if (isVersion(release.minVersion) && compareVersions(current, release.minVersion) < 0) {
    return {
      block: true,
      offer: false,
      version: release.minVersion,
      url,
      message: `This version (${current}) is no longer supported. Install ${release.minVersion} or newer.`,
    };
  }
  if (isVersion(release.version) && compareVersions(current, release.version) < 0) {
    return {
      block: false,
      offer: true,
      version: release.version,
      url,
      message: `Version ${release.version} is available.`,
    };
  }
  return idle;
}

function utcDay(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return null;
  }
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    return null;
  }
  return date.getTime();
}

function withinWindow(notice, now) {
  const today = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  if (notice.startsAt != null) {
    const start = utcDay(notice.startsAt);
    if (start === null || start > today) {
      return false;
    }
  }
  if (notice.endsAt != null) {
    const end = utcDay(notice.endsAt);
    if (end === null || end < today) {
      return false;
    }
  }
  return true;
}

function noticeMessage(value) {
  if (typeof value !== "string") {
    return null;
  }
  const message = value.trim();
  if (!message || message.length > 500 || /[<>]/.test(message)) {
    return null;
  }
  return message;
}

function parseNotice(entry) {
  if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
    return null;
  }
  if (typeof entry.id !== "string" || !NOTICE_ID_RE.test(entry.id)) {
    return null;
  }
  const message = noticeMessage(entry.message);
  if (!message) {
    return null;
  }
  if (entry.url != null && !isHttpsUrl(entry.url)) {
    return null;
  }
  return {
    id: entry.id,
    message,
    url: isHttpsUrl(entry.url) ? entry.url : null,
    startsAt: entry.startsAt == null ? null : entry.startsAt,
    endsAt: entry.endsAt == null ? null : entry.endsAt,
  };
}

function parseNotices(text) {
  if (typeof text !== "string") {
    return [];
  }
  let data;
  try {
    data = JSON.parse(text);
  } catch (_error) {
    return [];
  }
  if (!data || typeof data !== "object" || !Array.isArray(data.notices)) {
    return [];
  }
  return data.notices.map(parseNotice).filter(Boolean);
}

function activeNotices(notices, now, dismissedIds) {
  const dismissed = new Set(dismissedIds);
  return notices
    .filter((notice) => !dismissed.has(notice.id) && withinWindow(notice, now))
    .slice(0, MAX_NOTICES);
}

function emptyState() {
  return { dismissedNotices: [], dismissedUpdate: null };
}

function loadState(text) {
  if (typeof text !== "string") {
    return emptyState();
  }
  try {
    const data = JSON.parse(text);
    const dismissedNotices = Array.isArray(data.dismissedNotices)
      ? data.dismissedNotices.filter((id) => typeof id === "string" && NOTICE_ID_RE.test(id))
      : [];
    return {
      dismissedNotices: dismissedNotices.slice(-100),
      dismissedUpdate: isVersion(data.dismissedUpdate) ? data.dismissedUpdate : null,
    };
  } catch (_error) {
    return emptyState();
  }
}

function withDismissedNotice(state, id) {
  if (state.dismissedNotices.includes(id)) {
    return state;
  }
  return {
    dismissedNotices: [...state.dismissedNotices, id].slice(-100),
    dismissedUpdate: state.dismissedUpdate,
  };
}

function withDismissedUpdate(state, version) {
  return { dismissedNotices: state.dismissedNotices, dismissedUpdate: version };
}

function shouldOfferUpdate(decision, state) {
  return Boolean(decision.offer && decision.version && decision.version !== state.dismissedUpdate);
}

function appDataDir(platform, env, home) {
  if (platform === "win32") {
    const base = env.APPDATA || path.join(home, "AppData", "Roaming");
    return path.join(base, APP_DATA_DIR_NAME);
  }
  if (platform === "darwin") {
    return path.join(home, "Library", "Application Support", APP_DATA_DIR_NAME);
  }
  return path.join(home, ".local", "share", "open-sustainability-analyst");
}

function statePath(platform = process.platform, env = process.env, home = os.homedir()) {
  return path.join(appDataDir(platform, env, home), "remote-state.json");
}

function readState(filePath) {
  try {
    return loadState(fs.readFileSync(filePath, "utf8"));
  } catch (_error) {
    return emptyState();
  }
}

function saveState(filePath, state) {
  const body = JSON.stringify(loadState(JSON.stringify(state)));
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const temporary = `${filePath}.tmp`;
  fs.writeFileSync(temporary, body);
  fs.renameSync(temporary, filePath);
}

function defaultRequest(url, redirectsLeft = 3) {
  assertAllowedManifestUrl(url);
  return new Promise((resolve, reject) => {
    const request = https.get(url, { timeout: 8000 }, (response) => {
      const status = response.statusCode || 0;
      if (status >= 300 && status < 400 && response.headers.location) {
        response.resume();
        if (redirectsLeft <= 0) {
          reject(new Error("manifest redirected too many times"));
          return;
        }
        const next = new URL(response.headers.location, url).toString();
        resolve(defaultRequest(next, redirectsLeft - 1));
        return;
      }
      if (status !== 200) {
        response.resume();
        reject(new Error(`manifest status ${status}`));
        return;
      }
      const chunks = [];
      let size = 0;
      response.on("data", (chunk) => {
        size += chunk.length;
        if (size > MAX_BYTES) {
          request.destroy();
          reject(new Error("manifest too large"));
          return;
        }
        chunks.push(chunk);
      });
      response.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    });
    request.on("error", reject);
    request.on("timeout", () => {
      request.destroy();
      reject(new Error("manifest timeout"));
    });
  });
}

async function fetchText(url, requestImpl = defaultRequest) {
  assertAllowedManifestUrl(url);
  const text = await requestImpl(url);
  if (typeof text !== "string" || text.length > MAX_BYTES) {
    throw new Error("manifest too large");
  }
  return text;
}

module.exports = {
  APP_DATA_DIR_NAME,
  NOTICES_URL,
  RELEASE_URL,
  activeNotices,
  appDataDir,
  assertAllowedManifestUrl,
  compareVersions,
  fetchText,
  loadState,
  parseNotices,
  parseRelease,
  readState,
  releaseDecision,
  saveState,
  shouldOfferUpdate,
  statePath,
  withDismissedNotice,
  withDismissedUpdate,
};
