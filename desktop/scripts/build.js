const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..', '..');
const DESKTOP = path.resolve(__dirname, '..');
const DIST = path.join(ROOT, 'dist');
const BINARIES = path.join(DESKTOP, 'src-tauri', 'binaries');

function run(cmd, opts = {}) {
  console.log(`> ${cmd}`);
  execSync(cmd, { stdio: 'inherit', cwd: opts.cwd || ROOT, ...opts });
}

function getTargetTriple() {
  // Rust >= 1.93 uses host-tuple, older versions use host-triple
  try {
    return execSync('rustc --print host-tuple', { encoding: 'utf-8' }).trim();
  } catch {
    return execSync('rustc --print host-triple', { encoding: 'utf-8' }).trim();
  }
}

// Step 1: Build Python backend with PyInstaller
console.log('\n=== Step 1: PyInstaller Build ===');
run('pyinstaller hq_job.spec --clean --noconfirm');

// Step 2: Copy sidecar binary with platform triple suffix
console.log('\n=== Step 2: Copy Sidecar Binary ===');
const triple = getTargetTriple();
console.log(`Target triple: ${triple}`);

const isWindows = process.platform === 'win32';
const srcExe = path.join(DIST, isWindows ? 'hq_job_server.exe' : 'hq_job_server');
const dstExe = path.join(BINARIES, `hq_job_server-${triple}${isWindows ? '.exe' : ''}`);

if (!fs.existsSync(srcExe)) {
  console.error(`ERROR: PyInstaller output not found: ${srcExe}`);
  process.exit(1);
}

fs.mkdirSync(BINARIES, { recursive: true });
fs.copyFileSync(srcExe, dstExe);
console.log(`Copied: ${srcExe} -> ${dstExe}`);

// Step 3: Install npm deps if needed
console.log('\n=== Step 3: npm install ===');
if (!fs.existsSync(path.join(DESKTOP, 'node_modules'))) {
  run('npm install', { cwd: DESKTOP });
}

// Step 4: Build Tauri app
console.log('\n=== Step 4: Tauri Build ===');
run('npx tauri build', { cwd: DESKTOP });

console.log('\n=== Build Complete ===');
console.log(`Output: ${path.join(DESKTOP, 'src-tauri', 'target', 'release', 'bundle')}`);
