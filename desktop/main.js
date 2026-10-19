const { app, BrowserWindow, dialog, shell } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const path = require("path");

const remote = require("./remote-manifest");

const URL_MARKER = "OSA_DESKTOP_URL=";

let pythonProcess = null;

function resourceDir() {
  return app.isPackaged ? process.resourcesPath : __dirname;
}

function repoDir() {
  if (app.isPackaged) {
    return process.resourcesPath;
  }
  return path.resolve(__dirname, "..");
}

function pythonBin() {
  const prefix = path.join(resourceDir(), "python");
  if (process.platform === "win32") {
    return path.join(prefix, "python.exe");
  }
  return path.join(prefix, "bin", "python3");
}

function launcherScript() {
  return path.join(resourceDir(), "run_app.py");
}

function stopPython() {
  if (pythonProcess && !pythonProcess.killed) {
    pythonProcess.kill();
    pythonProcess = null;
  }
}

function waitForUrl(child) {
  return new Promise((resolve, reject) => {
    let buffer = "";
    let settled = false;
    const onData = (chunk) => {
      buffer += chunk.toString();
      const line = buffer
        .split(/\r?\n/)
        .find((entry) => entry.startsWith(URL_MARKER));
      if (!line) {
        return;
      }
      settled = true;
      child.stdout.off("data", onData);
      resolve(line.slice(URL_MARKER.length).trim());
    };
    child.stdout.on("data", onData);
    child.on("exit", (code) => {
      if (!settled) {
        reject(new Error(`Python exited before printing ${URL_MARKER} (code ${code})`));
      }
    });
  });
}

function waitForHealth(targetUrl) {
  const healthUrl = new URL("/_stcore/health", targetUrl);
  const attempts = 120;
  return new Promise((resolve, reject) => {
    const tryOnce = (left) => {
      const request = http.get(healthUrl, (response) => {
        response.resume();
        if (response.statusCode === 200) {
          resolve();
          return;
        }
        if (left <= 0) {
          reject(new Error(`Streamlit health returned ${response.statusCode}`));
          return;
        }
        setTimeout(() => tryOnce(left - 1), 500);
      });
      request.on("error", () => {
        if (left <= 0) {
          reject(new Error("Streamlit health check failed"));
          return;
        }
        setTimeout(() => tryOnce(left - 1), 500);
      });
    };
    tryOnce(attempts);
  });
}

function remoteContent() {
  return Promise.all([
    remote.fetchText(remote.RELEASE_URL).catch(() => null),
    remote.fetchText(remote.NOTICES_URL).catch(() => null),
  ]).then(([releaseText, noticesText]) => {
    const decision = remote.releaseDecision(app.getVersion(), remote.parseRelease(releaseText));
    const filePath = remote.statePath();
    const state = remote.readState(filePath);
    return {
      decision,
      filePath,
      state,
      offer: remote.shouldOfferUpdate(decision, state) ? decision : null,
      notices: remote.activeNotices(
        remote.parseNotices(noticesText),
        new Date(),
        state.dismissedNotices,
      ),
    };
  });
}

async function showForcedUpdate(decision) {
  const buttons = decision.url ? ["Download update", "Quit"] : ["Quit"];
  const options = {
    type: "warning",
    buttons,
    defaultId: 0,
    cancelId: buttons.length - 1,
    noLink: true,
    title: "Update required",
    message: "Open Sustainability Analyst needs an update",
    detail: decision.message,
  };
  if (decision.url) {
    options.detail = `${decision.message}\n\n${decision.url}`;
  }
  const { response } = await dialog.showMessageBox(options);
  if (decision.url && response === 0) {
    await shell.openExternal(decision.url);
  }
}

async function showChoice(title, message, url, confirmLabel) {
  const buttons = url ? [confirmLabel, "Close"] : ["Close"];
  const options = {
    type: "info",
    buttons,
    defaultId: buttons.length - 1,
    cancelId: buttons.length - 1,
    noLink: true,
    title,
    message,
  };
  if (url) {
    options.detail = url;
  }
  const { response } = await dialog.showMessageBox(options);
  if (url && response === 0) {
    await shell.openExternal(url);
  }
}

async function showOptionalRemote(content) {
  let state = content.state;
  if (content.offer) {
    await showChoice("Update available", content.offer.message, content.offer.url, "Download");
    state = remote.withDismissedUpdate(state, content.offer.version);
    remote.saveState(content.filePath, state);
  }
  for (const notice of content.notices) {
    await showChoice("Open Sustainability Analyst", notice.message, notice.url, "Open");
    state = remote.withDismissedNotice(state, notice.id);
    remote.saveState(content.filePath, state);
  }
}

async function openWindow() {
  const content = await remoteContent();
  if (content.decision.block) {
    await showForcedUpdate(content.decision);
    app.quit();
    return;
  }

  const binary = pythonBin();
  const script = launcherScript();
  if (!fs.existsSync(binary) || !fs.existsSync(script)) {
    dialog.showErrorBox(
      "Desktop runtime missing",
      "Run desktop/build_python.sh before starting the app.",
    );
    app.quit();
    return;
  }

  pythonProcess = spawn(binary, [script], {
    cwd: repoDir(),
    windowsHide: true,
    env: {
      ...process.env,
      PYTHONDONTWRITEBYTECODE: "1",
      PYTHONNOUSERSITE: "1",
    },
  });
  pythonProcess.stderr.on("data", (chunk) => {
    process.stderr.write(chunk);
  });

  const targetUrl = await waitForUrl(pythonProcess);
  console.log(targetUrl);
  await waitForHealth(targetUrl);

  if (process.platform === "darwin" && app.dock) {
    app.dock.setIcon(path.join(__dirname, "build", "icon.png"));
  }

  const window = new BrowserWindow({
    width: 1280,
    height: 860,
    title: "Open Sustainability Analyst",
    icon: path.join(__dirname, "build", "icon.png"),
  });
  window.on("closed", stopPython);
  await window.loadURL(targetUrl);
  console.log("OSA_DESKTOP_WINDOW=open");
  try {
    await showOptionalRemote(content);
  } catch (error) {
    console.error(error);
  }
}

app.on("before-quit", stopPython);
app.on("window-all-closed", () => {
  app.quit();
});

app.whenReady().then(openWindow).catch((error) => {
  dialog.showErrorBox("Open Sustainability Analyst failed to start", String(error));
  app.quit();
});
