import { build } from 'esbuild';
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const dist = join(root, 'dist');
const version = (await readFile(join(root, 'VERSION'), 'utf8')).trim();

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

const bundleName = `assets/app-${version}.js`;
await mkdir(join(dist, 'assets'), { recursive: true });

await build({
  entryPoints: [join(root, 'scripts/build-entry.jsx')],
  bundle: true,
  minify: true,
  sourcemap: true,
  format: 'iife',
  outfile: join(dist, bundleName),
  inject: [join(root, 'scripts/build/react-shim.js')],
  jsx: 'transform',
  target: ['es2019'],
  logLevel: 'info',
});

for (const file of ['styles.css', 'favicon.svg', 'manifest.js', 'daf.html']) {
  await cp(join(root, file), join(dist, file));
}
await cp(join(root, 'modules'), join(dist, 'modules'), { recursive: true });

let html = await readFile(join(root, 'index.html'), 'utf8');
html = html
  .replace(/manifest\.js\?v=[^"]+/g, `manifest.js?v=${version}`)
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/react[^\n]+<\/script>/g, '')
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/react-dom[^\n]+<\/script>/g, '')
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/@babel[^\n]+<\/script>/g, '')
  .replace(/\n\s*<script type="text\/babel" src="tweaks-panel\.jsx\?v=[^"]+"><\/script>/g, '')
  .replace(/\n\s*<script type="text\/babel" src="app\.jsx\?v=[^"]+"><\/script>/g, `\n  <script src="${bundleName}"></script>`);

await writeFile(join(dist, 'index.html'), html);
console.log(`Built static site in dist/ with ${bundleName}`);
