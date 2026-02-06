const tsParser = require('@typescript-eslint/parser');
const tsPlugin = require('@typescript-eslint/eslint-plugin');

module.exports = [
  {
    ignores: ['node_modules/**', 'dist/**', '**/*.d.ts'],
  },
  {
    files: ['components/**/*.ts', 'components/**/*.tsx', 'common/**/*.ts', 'patterns/**/*.ts'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      'no-debugger': 'error',
      'no-dupe-keys': 'error',
      'no-duplicate-imports': 'error',
      'no-unreachable': 'error',
      '@typescript-eslint/no-redeclare': 'error',
    },
  },
];
