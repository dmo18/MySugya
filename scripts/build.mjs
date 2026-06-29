import { build } from 'esbuild';
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const dist = join(root, 'dist');
const version = (await readFile(join(root, 'VERSION'), 'utf8')).trim();
const appPath = resolve(root, 'app.jsx');
const dataScriptPattern = /^modules\/[a-z0-9_-]+\/learning_data\.js$/;

function validateManifestDataScripts(source) {
  const matches = [...source.matchAll(/dataScript\s*:\s*"([^"]+)"/g)];
  if (!matches.length) {
    throw new Error('manifest.js does not declare any module dataScript values');
  }
  for (const match of matches) {
    const dataScript = match[1];
    if (!dataScriptPattern.test(dataScript)) {
      throw new Error(`manifest.js has unsafe module dataScript path: ${dataScript}`);
    }
  }
}

validateManifestDataScripts(await readFile(join(root, 'manifest.js'), 'utf8'));

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
        let before = contents;
        // Replace only the first brand div (Chrome component) with a home-link anchor.
        // LandingPage has an identical div that intentionally stays as a div.
        contents = contents.replace(
          /<div className="brand">([\s\S]*?)<\/div>/,
          (_, inner) => `<a className="brand" href="./" title="Back to index" aria-label="Back to index" style={{ color: "inherit", textDecoration: "none" }}>${inner}</a>`
        );
        if (contents === before) {
          throw new Error('homeLinkPlugin: brand div not found in app.jsx - check for source drift');
        }

        before = contents;
        contents = contents.replace(
          '\n// Lazy-load a module\'s data script once; resolves when its globals are live.\nfunction loadModuleData(mod) {',
          '\nfunction isAllowedModuleDataScript(mod) {\n  if (!mod || typeof mod.id !== "string" || typeof mod.dataScript !== "string") return false;\n  return /^[a-z0-9_-]+$/.test(mod.id) && mod.dataScript === "modules/" + mod.id + "/learning_data.js";\n}\n\n// Lazy-load a module\'s data script once; resolves when its globals are live.\nfunction loadModuleData(mod) {'
        );
        if (contents === before) {
          throw new Error('homeLinkPlugin: loadModuleData injection point not found in app.jsx - check for source drift');
        }

        before = contents;
        contents = contents.replace(
          '    if (!mod || !mod.id || typeof mod.dataScript !== "string" || !mod.dataScript) {\n      reject(new Error("loadModuleData: invalid module descriptor"));\n      return;\n    }',
          '    if (!mod || !mod.id || typeof mod.dataScript !== "string" || !mod.dataScript) {\n      reject(new Error("loadModuleData: invalid module descriptor"));\n      return;\n    }\n    if (!isAllowedModuleDataScript(mod)) {\n      reject(new Error("loadModuleData: unsafe dataScript path for " + mod.id));\n      return;\n    }'
        );
        if (contents === before) {
          throw new Error('homeLinkPlugin: loadModuleData guard not found in app.jsx - check for source drift');
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
