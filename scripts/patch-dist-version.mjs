import { readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const version = (await readFile(join(root, 'VERSION'), 'utf8')).trim();
const dataPath = join(root, 'dist/modules/yoma/learning_data.js');

let data = await readFile(dataPath, 'utf8');
const next = data.replace(
  /const DATA_VERSION = "[^"]+";/,
  `const DATA_VERSION = "${version}";`
);

if (next === data) {
  throw new Error('Could not find DATA_VERSION in dist/modules/yoma/learning_data.js');
}

await writeFile(dataPath, next);
console.log(`Patched dist learning_data.js DATA_VERSION to ${version}`);
