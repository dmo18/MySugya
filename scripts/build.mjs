import { build } from 'esbuild';
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const dist = join(root, 'dist');
const version = (await readFile(join(root, 'VERSION'), 'utf8')).trim();
const appPath = resolve(root, 'app.jsx');

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

const bundleName = `assets/app-${version}.js`;
await mkdir(join(dist, 'assets'), { recursive: true });

const homeLinkPlugin = {
  name: 'home-link',
  setup(build) {
    build.onLoad({ filter: /app\.jsx$/ }, async (args) => {
      let contents = await readFile(args.path, 'utf8');
      if (resolve(args.path) === appPath) {
        const before = contents;
        // Replace only the first brand div (Chrome component) with a home-link anchor.
        // LandingPage has an identical div that intentionally stays as a div.
        contents = contents.replace(
          /<div className="brand">([\s\S]*?)<\/div>/,
          (_, inner) => `<a className="brand" href="./" title="Back to index" aria-label="Back to index" style={{ color: "inherit", textDecoration: "none" }}>${inner}</a>`
        );
        if (contents === before) {
          throw new Error('homeLinkPlugin: brand div not found in app.jsx - check for source drift');
        }
      }
      return { contents, loader: 'jsx' };
    });
  },
};

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
  plugins: [homeLinkPlugin],
  define: { '__MYSUGYA_PLATFORM_VERSION__': JSON.stringify(version) },
});

for (const file of ['styles.css', 'favicon.svg', 'manifest.js', 'daf.html']) {
  await cp(join(root, file), join(dist, file));
}
await cp(join(root, 'modules'), join(dist, 'modules'), { recursive: true });

let html = await readFile(join(root, 'index.html'), 'utf8');
html = html
  .replace(/manifest\.js(?:\?v=[^"]*)?/g, `manifest.js?v=${version}`)
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/react[^\n]+<\/script>/g, '')
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/react-dom[^\n]+<\/script>/g, '')
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/@babel[^\n]+<\/script>/g, '')
  .replace(/\n\s*<script type="text\/babel" src="tweaks-panel\.jsx(?:\?v=[^"]+)?"><\/script>/g, '')
  .replace(/\n\s*<script type="text\/babel" src="app\.jsx(?:\?v=[^"]+)?"><\/script>/g, `\n  <script src="${bundleName}"></script>`);

await writeFile(join(dist, 'index.html'), html);
console.log(`Built static site in dist/ with ${bundleName}`);
