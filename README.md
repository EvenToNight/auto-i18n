Auto Translate i18n Files

Automatically translates JS/TS localization files using deep-translator.

Strings with comments containing [ignore18n] immediately after are skipped.

Usage:

- uses: eventonight/auto-i18n@v1
  with:
    source: 'en'
    targets: 'it,fr'
    input-file: 'i18n/locale/en.ts'

Inputs:

source       : Source language code (e.g., en)
targets      : Comma-separated target languages (e.g., it,fr)
input-file   : Path to the JS/TS file to translate

Ignore Strings:

Add [ignore18n] in a comment after a string to skip translation:

brandName: 'EvenToNight', // [ignore18n]

"EvenToNight" -> not translated
Other strings -> translated
