import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const htmlPath = join(root, 'dist', 'index.html');
const html = await readFile(htmlPath, 'utf8');

const forbidden = [
  'text/babel',
  'babel.min.js',
  'react.development.js',
  'react-dom.development.js',
];

const matches = forbidden.filter((token) => html.includes(token));

if (matches.length) {
  console.error(`dist/index.html contains development-only dependencies: ${matches.join(', ')}`);
  process.exit(1);
}

console.log('dist/index.html is free of development-only Babel and React loaders.');
