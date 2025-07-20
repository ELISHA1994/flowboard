module.exports = {
  // Python files in backend
  'apps/backend/**/*.py': (filenames) => [
    `cd apps/backend && ruff check ${filenames.map(f => f.replace('apps/backend/', '')).join(' ')} --fix`,
    `cd apps/backend && ruff format ${filenames.map(f => f.replace('apps/backend/', '')).join(' ')}`,
    `cd apps/backend && mypy ${filenames.map(f => f.replace('apps/backend/', '')).join(' ')}`
  ],
  
  // JSON files
  '**/*.json': ['prettier --write'],
  
  // YAML files
  '**/*.{yml,yaml}': ['prettier --write'],
  
  // Markdown files
  '**/*.md': ['prettier --write'],
  
  // JavaScript/TypeScript files (for future use)
  '**/*.{js,jsx,ts,tsx}': ['prettier --write', 'eslint --fix'],
  
  // Docker files
  '**/Dockerfile*': (filenames) => 
    filenames.map(filename => `docker run --rm -i hadolint/hadolint < ${filename} || true`)
};