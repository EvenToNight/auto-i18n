# Auto i18n Translator

Automatically translate JavaScript/TypeScript localization files using Google Translate.

## Features

- 🌍 Automatic translation to multiple languages
- 🔄 Preserves existing translations (only translates new/updated keys)
- 🚫 Skip specific strings with `[ignorei18n]` comments
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
| `update_only_new` | Only translate new keys, preserve existing translations | ❌ No | `true` |
| `github_token` | GitHub token for authentication | ❌ No | `${{ github.token }}` |

## How it works

1. **Change Detection**: Checks if the source file has changed (can be disabled)
2. **Load Existing Translations**: Reads existing target files to preserve manual edits
3. **Translate**: Translates only new or updated keys using Google Translate
4. **Write Files**: Creates/updates target language files (e.g., `it.ts`, `fr.ts`)
5. **Commit & Push**: Automatically commits and pushes changes with `[skip ci]`

## Skip Translation

Add `// [ignorei18n]` after any string to skip translation:

```typescript
export default {
  brandName: 'MyApp', // [ignorei18n]
  welcome: 'Welcome',  // ← will be translated
}
```

**Result:**
```typescript
// it.ts
export default {
  brandName: 'MyApp', // [ignorei18n]  ← not translated
  welcome: 'Benvenuto',  // ← translated
}
```

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
