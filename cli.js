#!/usr/bin/env node

const { execSync, spawnSync } = require("child_process");
const path = require("path");

const args = process.argv.slice(2);

function getArg(name) {
  const flag = `--${name}`;
  const idx = args.indexOf(flag);
  if (idx !== -1 && args[idx + 1]) return args[idx + 1];
  const prefix = `--${name}=`;
  const match = args.find((a) => a.startsWith(prefix));
  return match ? match.slice(prefix.length) : null;
}

function printHelp() {
  console.log(`
Usage: auto-i18n --source <lang> --targets <langs> --file <path> [options]

Required:
  --source   <lang>    Source language code (e.g. en)
  --targets  <langs>   Comma-separated target languages (e.g. it,fr)
  --file     <path>    Path to the source i18n file

Options:
  --evaluate-changes   Compare against git HEAD to only translate changed keys (default: false)
  --previous-head      Git commit hash to compare against (requires --evaluate-changes)
  --current-head       Current git commit hash (requires --evaluate-changes)
  --help               Show this help message
`);
}

if (args.includes("--help") || args.includes("-h")) {
  printHelp();
  process.exit(0);
}

const source = getArg("source");
const targets = getArg("targets");
const inputFile = getArg("file");

if (!source || !targets || !inputFile) {
  console.error("Error: --source, --targets, and --file are required.\n");
  printHelp();
  process.exit(1);
}

const evaluateChanges = args.includes("--evaluate-changes");
const previousHead = getArg("previous-head") || "";
const currentHead = getArg("current-head") || "";

const actionDir = path.dirname(require.resolve("./package.json"));
const requirementsFile = path.join(actionDir, "requirements.txt");
const translatorScript = path.join(actionDir, "translator.py");

// Install Python dependencies
console.log("Installing Python dependencies...");
const pip = spawnSync("pip", ["install", "-q", "-r", requirementsFile], {
  stdio: "inherit",
});
if (pip.status !== 0) {
  // Try pip3
  const pip3 = spawnSync("pip3", ["install", "-q", "-r", requirementsFile], {
    stdio: "inherit",
  });
  if (pip3.status !== 0) {
    console.error("Error: Could not install dependencies via pip or pip3.");
    process.exit(1);
  }
}

// Run translator
const python = spawnSync(
  process.platform === "win32" ? "python" : "python3",
  [translatorScript],
  {
    stdio: "inherit",
    cwd: process.cwd(),
    env: {
      ...process.env,
      INPUT_SOURCE: source,
      INPUT_TARGETS: targets,
      INPUT_INPUT_FILE: inputFile,
      INPUT_EVALUATE_CHANGES: evaluateChanges ? "true" : "false",
      INPUT_PREVIOUS_HEAD: previousHead,
      INPUT_CURRENT_HEAD: currentHead,
    },
  }
);

process.exit(python.status ?? 1);
