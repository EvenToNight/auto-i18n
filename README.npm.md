# @eventonight/auto-i18n

Automatically translate JavaScript/TypeScript localization files using Google Translate.

> **Prerequisites:** Python 3 and pip must be installed on your system.

## Installation

```bash
npm install -g @eventonight/auto-i18n
# or use directly with npx
npx @eventonight/auto-i18n --help
```

## CLI Usage

```bash
auto-i18n --source <lang> --targets <langs> --file <path> [options]
```

### Required flags

| Flag | Description | Example |
|------|-------------|---------|
| `--source` | Source language code | `en` |
| `--targets` | Comma-separated target languages | `it,fr,es` |
| `--file` | Path to the source i18n file | `locales/en.ts` |

### Options

| Flag | Description |
|------|-------------|
| `--evaluate-changes` | Only translate keys that changed since last commit |
| `--previous-head` | Git commit hash to compare against (used with `--evaluate-changes`) |
| `--current-head` | Current git commit hash (used with `--evaluate-changes`) |
| `--help` | Show help message |

### Examples

**Translate all keys:**
```bash
auto-i18n --source en --targets it,fr,es --file locales/en.ts
```

**Only translate changed keys (smart mode):**
```bash
auto-i18n --source en --targets it,fr,es --file locales/en.ts --evaluate-changes
```

## GitHub Action

This package is also available as a GitHub Action for automatic translation on push:

```yaml
name: Translate i18n files
on:
  push:
    branches:
      - main

jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: eventonight/auto-i18n@v1
        with:
          source: 'en'
          targets: 'it,fr,es'
          input_file: 'locales/en.ts'
```

For the full list of Action inputs see the [GitHub repository](https://github.com/EvenToNight/auto-i18n).

## Preserve Custom Translations

Use `// [ignorei18n]` to prevent keys from being translated.

**In the source file** — skips translation for all languages:
```typescript
// locales/en.ts
export default {
  brandName: 'MyApp', // [ignorei18n] ← won't be translated
  welcome: 'Welcome',
}
```

**In a destination file** — preserves your custom translation:
```typescript
// locales/it.ts
export default {
  welcome: 'Ciao!', // [ignorei18n] ← won't be overwritten
}
```

## File Format

Supports standard JS/TS i18n file formats:

```typescript
export default {
  key1: 'value1',
  nested: {
    key2: 'value2',
  },
}
```

## Supported Languages

All languages supported by Google Translate. Common codes: `en`, `it`, `fr`, `es`, `de`, `pt`, `ja`.

[Full list of language codes](https://cloud.google.com/translate/docs/languages)
