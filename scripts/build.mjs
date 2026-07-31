import { build } from 'esbuild';
import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';

const root = new URL('..', import.meta.url).pathname;
const require = createRequire(import.meta.url);
const { listModules, resolveModule } = require('../shared/module_resolver.js');

// --module <key>: build only modules/<key> instead of the whole modules/
// tree. --out <path>: write output to an isolated directory instead of the
// default production dist/. --search-root <path> (or the
// MYSUGYA_MODULE_SEARCH_ROOT env var, same convention worker_pipeline.py
// established in Phase 3 Step 3A): resolve --module's descriptor from a
// directory other than modules/ - the only way to build a module (e.g.
// the Phase 3 Step 5 fixture) that intentionally lives outside modules/
// so the modules/*/module.json glob never discovers it. Only legal
// together with --module; there is no "search every module under an
// alternate root" mode. A module whose module.json declares
// publishable:false may never build into the default dist/ path (see the
// publishable-flag guard below) - this is the defense-in-depth backstop
// that keeps a non-publishable (e.g. synthetic fixture) module from ever
// landing where GitHub Pages deploys from, in addition to the fixture's
// own planned location outside modules/ entirely.
function parseArgs(argv) {
  const args = { module: null, out: null, searchRoot: null };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--module') args.module = argv[++i];
    else if (arg.startsWith('--module=')) args.module = arg.slice('--module='.length);
    else if (arg === '--out') args.out = argv[++i];
    else if (arg.startsWith('--out=')) args.out = arg.slice('--out='.length);
    else if (arg === '--search-root') args.searchRoot = argv[++i];
    else if (arg.startsWith('--search-root=')) args.searchRoot = arg.slice('--search-root='.length);
  }
  return args;
}

const cli = parseArgs(process.argv.slice(2));
const searchRootRaw = cli.searchRoot ?? process.env.MYSUGYA_MODULE_SEARCH_ROOT ?? null;
if (searchRootRaw && !cli.module) {
  throw new Error('build.mjs: --search-root is only legal together with --module - there is no "search every module under an alternate root" mode.');
}
const searchRootAbs = searchRootRaw ? resolve(process.cwd(), searchRootRaw) : null;
const defaultDist = join(root, 'dist');
const dist = cli.out ? resolve(process.cwd(), cli.out) : defaultDist;
const isDefaultDist = resolve(dist) === resolve(defaultDist);

if (resolve(dist) === resolve(root)) {
  throw new Error(`build.mjs: --out must not resolve to the repository root (${root})`);
}

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

let selectedModule = null;
let selectedModulePhysicalDir = null;
let selectedDescriptor = null;
if (cli.module) {
  const descriptor = resolveModule(cli.module, root, searchRootAbs ?? undefined);
  selectedDescriptor = descriptor;
  selectedModulePhysicalDir = searchRootAbs
    ? join(searchRootAbs, cli.module)
    : join(root, 'modules', cli.module);
  if (descriptor.publishable === false && isDefaultDist) {
    throw new Error(
      `build.mjs: module ${JSON.stringify(cli.module)} has publishable=false in its module.json ` +
      `- refusing to build it into the default production dist/ directory. Pass --out <path> to ` +
      `build it to an isolated, non-production output directory instead.`
    );
  }
  selectedModule = cli.module;
} else {
  const nonPublishable = listModules(root).filter(
    (key) => resolveModule(key, root).publishable === false
  );
  if (nonPublishable.length && isDefaultDist) {
    throw new Error(
      `build.mjs: refusing an unqualified build - non-publishable module(s) present under ` +
      `modules/: ${nonPublishable.join(', ')}. Pass --module <key> to build a single module, or ` +
      `--out <path> to build all modules to an isolated (non-production) output directory.`
    );
  }
}

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

for (const file of ['styles.css', 'favicon.svg', 'daf.html']) {
  await cp(join(root, file), join(dist, file));
}
if (searchRootAbs) {
  // An isolated build of a module resolved outside modules/ (the Step 5/6
  // fixture) can never appear in the real, committed manifest.js - that
  // file is never touched. Without SOME manifest entry naming it, the
  // app shell's `?module=` lookup (app.jsx's MYSUGYA_MANIFEST.find) would
  // fall through to the landing page, making an isolated fixture build
  // unrenderable and therefore untestable. Synthesize a manifest.js
  // containing only this one module's entry, from fields already present
  // on its own resolved (and independently validated) descriptor - not
  // hand-maintained, not written to the real manifest.js, and never
  // reachable unless --search-root is explicitly passed.
  const learningDataText = await readFile(join(selectedModulePhysicalDir, 'learning_data.js'), 'utf8');
  const dataVersionMatch = learningDataText.match(/const DATA_VERSION = "([^"]+)"/);
  const isolatedManifest = `const MYSUGYA_MANIFEST = ${JSON.stringify([{
    id: selectedDescriptor.key,
    title: selectedDescriptor.displayNameEn,
    title_he: selectedDescriptor.displayNameHe ?? '',
    seder: selectedDescriptor.seder ?? '',
    dafRange: selectedDescriptor.dafRange,
    totalDaf: selectedDescriptor.totalDaf,
    dataScript: `modules/${selectedDescriptor.key}/learning_data.js`,
    dataVersion: dataVersionMatch ? dataVersionMatch[1] : '1.0',
  }], null, 2)};\n`;
  await writeFile(join(dist, 'manifest.js'), isolatedManifest);
} else {
  await cp(join(root, 'manifest.js'), join(dist, 'manifest.js'));
}
await mkdir(join(dist, 'shared'), { recursive: true });
await cp(join(root, 'shared/rashi_association.js'), join(dist, 'shared/rashi_association.js'));
if (selectedModule) {
  await cp(
    selectedModulePhysicalDir,
    join(dist, 'modules', selectedModule),
    { recursive: true }
  );
} else {
  await cp(join(root, 'modules'), join(dist, 'modules'), { recursive: true });
}

let html = await readFile(join(root, 'index.html'), 'utf8');
html = html
  .replace(/manifest\.js(?:\?v=[^"]*)?/g, `manifest.js?v=${version}`)
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/react[^\n]+<\/script>/g, '')
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/react-dom[^\n]+<\/script>/g, '')
  .replace(/\n\s*<script src="https:\/\/unpkg\.com\/@babel[^\n]+<\/script>/g, '')
  .replace(/shared\/rashi_association\.js(?:\?v=[^"]*)?/g, `shared/rashi_association.js?v=${version}`)
  .replace(/\n\s*<script type="text\/babel" src="tweaks-panel\.jsx(?:\?v=[^"]+)?"><\/script>/g, '')
  .replace(/\n\s*<script type="text\/babel" src="app\.jsx(?:\?v=[^"]+)?"><\/script>/g, `\n  <script src="${bundleName}"></script>`);

await writeFile(join(dist, 'index.html'), html);
const distLabel = isDefaultDist ? 'dist/' : dist;
const moduleLabel = selectedModule ? ` (module: ${selectedModule})` : '';
console.log(`Built static site in ${distLabel} with ${bundleName}${moduleLabel}`);
