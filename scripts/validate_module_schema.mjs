#!/usr/bin/env node
/**
 * validate_module_schema.mjs - generic, module-agnostic schema-completeness
 * and capability-driven validator (Phase 3 six-row closure campaign).
 *
 * Unlike modules/yoma/scripts/validate_schema_completeness.py (PER_MODULE
 * tier, reads the pre-generation *.learning.json enrichment files), this
 * validates the GENERATED learning_data.js - the artifact that actually
 * ships and renders - for any resolvable module, real or fixture.
 *
 * Two things it checks:
 *   1. Schema completeness: every sugya carries display.title and the
 *      required learning.* fields shared/schema_map.js declares, mirroring
 *      validate_schema_completeness.py's required-field list.
 *   2. Capability-driven content: capabilities.rashi.enabled and
 *      capabilities.literalTranslation.enabled must agree with what is
 *      actually present in the corpus - a module that declares a
 *      capability disabled must carry zero of that capability's content
 *      (rashiLines / line.en_lit), and a module that declares it enabled
 *      must carry at least some. This is what makes literal-translation
 *      behavior capability-driven (Phase 3 acceptance row 17), the same
 *      way resolveRashiModule() already made Rashi behavior
 *      capability-driven in Step 3D - here expressed as a content-vs-
 *      declaration consistency check rather than a resolution-time error,
 *      since a validator's job is checking data, not gating a tool call.
 *
 * Usage:
 *   node scripts/validate_module_schema.mjs --module yoma
 *   node scripts/validate_module_schema.mjs --module demotractate --search-root tests/fixtures/modules
 */
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { resolveModule } = require('../shared/module_resolver.js');

function parseArgs(argv) {
  const args = { module: null, searchRoot: null };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--module') args.module = argv[++i];
    else if (argv[i] === '--search-root') args.searchRoot = argv[++i];
  }
  if (!args.module) {
    console.error('Usage: validate_module_schema.mjs --module <key> [--search-root <path>]');
    process.exit(2);
  }
  return args;
}

const ROOT = resolve(new URL('..', import.meta.url).pathname);
const opts = parseArgs(process.argv.slice(2));
const searchRootAbs = opts.searchRoot ? resolve(process.cwd(), opts.searchRoot) : undefined;

let descriptor;
try {
  descriptor = resolveModule(opts.module, ROOT, searchRootAbs);
} catch (e) {
  console.error(`FAILED: ${e.code}: ${e.message}`);
  process.exit(1);
}

// Physical location: honors --search-root exactly like build.mjs and
// worker_pipeline.py's set_active_module() do - paths.root is always the
// logical "modules/<key>" string, never assumed to equal the real directory.
const physicalRoot = searchRootAbs ? join(searchRootAbs, opts.module) : join(ROOT, 'modules', opts.module);
const learningDataFileName = descriptor.paths.learningDataFile.split('/').pop();
const learningDataPath = join(physicalRoot, learningDataFileName);

// learning_data.js is a plain JS script (const X = {...}; possibly with
// unquoted-key object literals, e.g. Yoma's), not JSON - loading it
// generically means letting Node's own parser handle it, not writing a
// bespoke object-literal parser. Appending an explicit module.exports to a
// scratch copy makes the file's top-level consts requirable, whether or
// not the original file already had its own export guard.
function loadModuleData(path) {
  const src = readFileSync(path, 'utf8');
  const scratchDir = mkdtempSync(join(tmpdir(), 'validate-module-schema-'));
  const scratchFile = join(scratchDir, 'dump.cjs');
  writeFileSync(scratchFile, src + '\nmodule.exports = { TRACTATE_META, DAF_CONTENT };\n');
  return require(scratchFile);
}

const { TRACTATE_META, DAF_CONTENT } = loadModuleData(learningDataPath);

const REQUIRED_DISPLAY_FIELDS = ['title'];
const REQUIRED_LEARNING_FIELDS = [
  'learnerQuestion', 'coreTension', 'coreMove',
  'ahaMoment', 'learningBlocker', 'memoryAnchor',
];
const REQUIRED_ARGUMENT_FLOW_FIELDS = ['id', 'type', 'label', 'text'];

function isBlank(v) {
  return v === undefined || v === null || (typeof v === 'string' && v.trim() === '');
}

const problems = [];
let sugyaCount = 0;
let argumentFlowCount = 0;
let rashiLineCount = 0;
let enLitCount = 0;
const dafIds = Object.keys(DAF_CONTENT);

for (const daf of dafIds) {
  const dafEntry = DAF_CONTENT[daf];
  for (const sug of dafEntry.sugyot || []) {
    sugyaCount++;
    const display = sug.display || {};
    const learning = sug.learning || {};
    const sugLabel = `${daf} ${sug.id || '<no id>'}`;

    for (const field of REQUIRED_DISPLAY_FIELDS) {
      if (isBlank(display[field])) problems.push(`${sugLabel}: missing display.${field}`);
    }
    for (const field of REQUIRED_LEARNING_FIELDS) {
      if (isBlank(learning[field])) problems.push(`${sugLabel}: missing learning.${field}`);
    }
    if (!learning.takeaway || isBlank(learning.takeaway.text)) {
      problems.push(`${sugLabel}: missing learning.takeaway.text`);
    }

    for (const step of sug.argumentFlow || []) {
      argumentFlowCount++;
      for (const field of REQUIRED_ARGUMENT_FLOW_FIELDS) {
        if (isBlank(step[field])) problems.push(`${sugLabel} step ${step.id || '?'}: missing argumentFlow.${field}`);
      }
    }
    for (const line of sug.lines || []) {
      if (!isBlank(line.en_lit)) enLitCount++;
    }
  }
  for (const _rl of dafEntry.rashiLines || []) {
    rashiLineCount++;
  }
}

const rashiEnabled = descriptor.capabilities.rashi.enabled;
const literalEnabled = descriptor.capabilities.literalTranslation.enabled;

if (rashiEnabled && rashiLineCount === 0) {
  problems.push('capabilities.rashi.enabled=true but zero rashiLines were found anywhere in the corpus');
}
if (!rashiEnabled && rashiLineCount > 0) {
  problems.push(`capabilities.rashi.enabled=false but ${rashiLineCount} rashiLines were found - a disabled capability must carry no content`);
}
if (literalEnabled && enLitCount === 0) {
  problems.push('capabilities.literalTranslation.enabled=true but zero en_lit fields were found anywhere in the corpus');
}
if (!literalEnabled && enLitCount > 0) {
  problems.push(`capabilities.literalTranslation.enabled=false but ${enLitCount} en_lit fields were found - a disabled capability must carry no content`);
}

console.log(`Module: ${opts.module} (${TRACTATE_META.title || TRACTATE_META.title_en || ''})`);
console.log(`Daf: ${dafIds.length}  Sugyot: ${sugyaCount}  ArgumentFlow steps: ${argumentFlowCount}`);
console.log(`capabilities.rashi.enabled=${rashiEnabled} rashiLines=${rashiLineCount}`);
console.log(`capabilities.literalTranslation.enabled=${literalEnabled} en_lit fields=${enLitCount}`);

if (problems.length) {
  console.error(`\nFAIL: ${problems.length} problem(s):`);
  for (const p of problems.slice(0, 50)) console.error(`  ${p}`);
  if (problems.length > 50) console.error(`  ... and ${problems.length - 50} more`);
  process.exit(1);
}

console.log('\nOK: schema complete and capability declarations match corpus content.');
