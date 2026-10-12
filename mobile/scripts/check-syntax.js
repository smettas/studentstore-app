// Lightweight syntax smoke-check using Node's parser via dynamic import is not suitable
// for all React Native transforms. Use `npx expo export --platform android` after install
// for a full Expo bundle check.
const fs = require('fs');
const path = require('path');

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(full) : [full];
  });
}

const sourceFiles = walk(path.join(__dirname, '..', 'src')).filter((file) => file.endsWith('.js'));
console.log(`Found ${sourceFiles.length} JavaScript source files. Run Expo export for parser/bundler validation.`);
