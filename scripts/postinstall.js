#!/usr/bin/env node

const fs = require("fs");
const https = require("https");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const defaultRepo = "https://github.com/dptech-corp/bohrium-skills";
const repo = (process.env.BOHRIUM_SKILLS_CLI_RELEASE_REPO || defaultRepo).replace(/\/+$/, "");
const pkg = require("../package.json");
const dryRun = process.argv.includes("--dry-run");
const skipSync = process.env.BOHRIUM_SKILLS_CLI_NO_POSTINSTALL_SYNC === "1";

function platformName() {
  const value = os.platform();
  if (value === "darwin") return "darwin";
  if (value === "linux") return "linux";
  if (value === "win32") return "windows";
  throw new Error(`unsupported platform: ${value}`);
}

function archName() {
  const value = os.arch();
  if (value === "x64") return "amd64";
  if (value === "arm64") return "arm64";
  throw new Error(`unsupported architecture: ${value}`);
}

function download(url, dest, redirects = 0) {
  if (redirects > 5) {
    throw new Error("too many redirects");
  }
  return new Promise((resolve, reject) => {
    const req = https.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        const next = new URL(res.headers.location, url).toString();
        download(next, dest, redirects + 1).then(resolve, reject);
        return;
      }
      if (res.statusCode !== 200) {
        res.resume();
        reject(new Error(`download failed with HTTP ${res.statusCode}: ${url}`));
        return;
      }
      const file = fs.createWriteStream(dest, { mode: 0o755 });
      res.pipe(file);
      file.on("finish", () => file.close(resolve));
      file.on("error", reject);
    });
    req.on("error", reject);
  });
}

async function main() {
  const goos = platformName();
  const goarch = archName();
  const exe = goos === "windows" ? ".exe" : "";
  const asset = `bohrium-skills-cli_${goos}_${goarch}${exe}`;
  const url = `${repo}/releases/download/v${pkg.version}/${asset}`;
  const binDir = path.join(__dirname, "..", "bin");
  const binPath = path.join(binDir, "bohrium-skills-cli");

  if (dryRun) {
    console.log(JSON.stringify({ url, binPath, skipSync }, null, 2));
    return;
  }

  fs.mkdirSync(binDir, { recursive: true });
  await download(url, binPath);
  fs.chmodSync(binPath, 0o755);

  if (skipSync) {
    console.log("bohrium-skills-cli: postinstall skill sync skipped by BOHRIUM_SKILLS_CLI_NO_POSTINSTALL_SYNC=1");
    return;
  }

  const result = spawnSync(binPath, ["install", "--lang", "zh", "--json"], {
    stdio: "inherit",
    env: process.env
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(`bohrium-skills-cli install failed with exit code ${result.status}`);
  }
}

main().catch((err) => {
  console.error(`bohrium-skills-cli postinstall failed: ${err.message}`);
  process.exit(1);
});
