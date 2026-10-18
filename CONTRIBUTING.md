# Contributing

Thanks for helping improve Free Tape Labels!

## Issues first

Please open an issue before starting larger work. Especially useful:

- **Missing label sheets or label printers**: brand, product number, and if possible the dimensions from the data sheet (page size, label width/height, margins, gaps, columns, rows).
- **Barcode problems**: library or scanner model, cartridge type, template, and whether the label was printed at 100 % scale.
- **Translation fixes**: language, the current text and your suggestion.

## Pull requests

1. Keep the app a single file (`src/free-tape-label.html`) without external requests at runtime.
2. Write UI strings in English. A new or changed string needs an entry in **every** dictionary (the English text is the key, see the README).
3. Run `python3 tools/build_site.py` and check the result in a browser, ideally in light and dark mode and on a narrow window.
4. Tick the CLA checkbox in the pull request description.

## Contributor License Agreement

Pull requests can only be merged if you agree to the [Contributor License Agreement](CLA.md). You keep the copyright to your contribution. The CLA allows the project to continue to offer the code under other licenses in the future (for example a commercial license next to the AGPL-3.0).

If you do not want to agree to the CLA, you can still open an issue describing the change, and it may be implemented independently.
