# Auto i18n Translator

Automatically translate JavaScript/TypeScript localization files using Google Translate.

## Features

- 🌍 Automatic translation to multiple languages
- 🚫 Preserve custom translations with `[ignorei18n]`
- 📦 Auto-commits and pushes translations
- ⚡ Smart change detection (only runs when source file changes and translates only modified keys)

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
      - uses: eventonight/auto-i18n@v1.4.0
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
| `node_version` | Node version to use for run pre commit npm command | ❌ No | `20` |
| `npm_working_directory` | Directory where is located package.json | ❌ No | `.` |
| `pre-commit-npm-command` | npm command to run before commit | ❌ No | `''` |

## How it works

### With Smart Change Detection (`evaluate_changes: true`, default)

1. **Git Diff Analysis**: Compares source file between commits
   - If no changes: exits without translation
   - If changes found: extracts modified keys from git diff
2. **Incremental Translation**: Only translates modified keys
   - Preserves existing translations for unchanged keys
   - Skips translation if `[ignorei18n]` marker is present
3. **Preserve Custom Translations**: Reads `[ignorei18n]` markers in source and destination files
4. **Write & Commit**: Updates only changed translations and commits with `[skip ci]`

### Without Change Detection (`evaluate_changes: false`)

1. **Full Translation**: Translates all keys from source file
   - Skips keys marked with `[ignorei18n]` in source file
2. **Preserve Custom Translations**: Reads `[ignorei18n]` markers in destination files
3. **Write & Commit**: Overwrites all target files and commits with `[skip ci]`

## Preserve Custom Translations

Use `// [ignorei18n]` to preserve translations or skip translation entirely:

### Skip translation for all languages (source file)

Add `[ignorei18n]` in the **source file** to prevent translation for all target languages:

```typescript
// locales/en.ts
export default {
  brandName: 'MyApp', // [ignorei18n] ← won't be translated to any language
  welcome: 'Welcome',
  goodbye: 'Goodbye',
}
```

All target files will keep `brandName: 'MyApp'` unchanged.

### Preserve custom translations (destination file)

Add `[ignorei18n]` in the **destination file** to preserve your custom translation:

```typescript
// locales/it.ts
export default {
  brandName: 'MyApp',
  welcome: 'Ciao!', // [ignorei18n] ← custom translation, won't be overwritten
  goodbye: 'Arrivederci',
}
```

When `en.ts` changes, `welcome` will keep your custom "Ciao!" translation.

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

## Example: Incremental Translation

When you modify only one key in your source file:

```diff
// locales/en.ts
export default {
  hello: 'Hello',
- goodbye: 'Goodbye',
+ goodbye: 'See you later',
  welcome: 'Welcome',
}
```

The action will:
- ✅ Detect that only `goodbye` changed
- ✅ Translate only `goodbye` to all target languages
- ✅ Keep existing translations for `hello` and `welcome`
- ✅ Preserve any keys marked with `[ignorei18n]`

## Notes

- Generated files are named `{lang}.ts` in the same directory as the source file
- Commits are made as `github-actions[bot]` with `[skip ci]` to avoid workflow loops
- Apostrophes in translations (e.g., `it's` → `it\'s`) are automatically escaped
- Set `evaluate_changes: false` to always translate all keys
