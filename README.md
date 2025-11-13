# Auto i18n Translator

Automatically translate JavaScript/TypeScript localization files using Google Translate.

## Features

- 🌍 Automatic translation to multiple languages
- 🚫 Preserve custom translations with `[ignorei18n]` in destination files
- 📦 Auto-commits and pushes translations
- ⚡ Smart change detection (only runs when source file changes)

## Usage

```yaml
name: Translate i18n files
on:
  push:
    branches:
      - main

jobs:
  translate:
    runs-on: ubuntu-22.0
    steps:
      - uses: eventonight/auto-i18n@v1.3.0
        with:
          source: 'en'
          targets: 'it,fr,es'
          input_file: 'locales/en.ts'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `source` | Source language code (e.g., `en`) | ✅ Yes | - |
| `targets` | Comma-separated target languages (e.g., `it,fr,es`) | ✅ Yes | - |
| `input_file` | Path to the source JS/TS file to translate | ✅ Yes | - |
| `previous_head` | Git commit hash to compare changes against | ❌ No | `${{ github.event.before }}` |
| `current_head` | Current Git commit hash | ❌ No | `${{ github.sha }}` |
| `evaluate_changes` | Check if input file has changes before translating | ❌ No | `true` |
| `github_token` | GitHub token for authentication | ❌ No | `${{ github.token }}` |

## How it works

1. **Change Detection**: Checks if the source file has changed since the last commit
   - If no changes: skips translation entirely
   - If changed: proceeds with translation for all target languages
2. **Load Preserved Keys**: Reads destination files to find keys marked with `[ignorei18n]`
3. **Translate**: Translates all strings from source, except those marked as ignored
4. **Write Files**: Creates/updates target language files (e.g., `it.ts`, `fr.ts`)
5. **Commit & Push**: Automatically commits and pushes changes with `[skip ci]`

## Preserve Custom Translations

Add `// [ignorei18n]` in the **destination file** to preserve custom translations:

**Source file (`en.ts`):**
```typescript
export default {
  brandName: 'MyApp', // [ignorei18n]
  welcome: 'Welcome',
  goodbye: 'Goodbye',
}
```

**Destination file with custom translation (`it.ts`):**
```typescript
export default {
  brandName: 'MyApp', // [ignorei18n]
  welcome: 'Ciao!', // [ignorei18n] ← custom translation, won't be overwritten
  goodbye: 'Arrivederci',
}
```

You can also use `[ignorei18n]` in the source file to skip translation for all languages.

## File Format

Supports standard JS/TS i18n file formats:

```typescript
export default {
  key1: 'value1',
  nested: {
    key2: 'value2',
    key3: 'value3',
  },
}
```

## Supported Languages

All languages supported by Google Translate. Common codes:
- `en` - English
- `it` - Italian
- `fr` - French
- `es` - Spanish
- `de` - German
- `pt` - Portuguese
- `ja` - Japanese

[Full list of language codes](https://cloud.google.com/translate/docs/languages)

## Notes

- Generated files are named `{lang}.ts` in the same directory as the source file
- Commits are made as `github-actions[bot]` with `[skip ci]` to avoid workflow loops
- Apostrophes in translations (e.g., `it's` → `it\'s`) are automatically escaped
