# Changelog

## [0.1.0] — 2026-03-13

### Added
- `QTrapArray`: rectangular grid of optical tweezers with optional boolean mask
  and per-trap Gaussian position jitter (`fuzz` parameter)
- `QLetterArray`: single dot-matrix character (A-Z, a-z, 0-9, space) rendered
  as an array of tweezers using a 5×7 bitmap font
- `QTextArray`: multi-character text string composed of `QLetterArray` instances
- Lowercase glyph set for `QLetterArray` (distinct from uppercase)
- `reshaping` / `reshaped` signals on `QTrapArray` and `QTextArray` to bracket
  trap-population changes
- Pre-push git hook running the full unit-test suite before every `git push`
- `pyproject.toml` packaging metadata and `pyfab` entry-point script
- Comprehensive unit-test suite (~700 tests) covering all trap classes,
  overlay, CGH, SLM, save/restore, and UI widgets

### Changed
- `QTrapOverlay.removeTrap` now iterates `group.leaves()` instead of direct
  children, correctly handling nested trap groups such as `QTextArray`

### Fixed
- Mask shape validation in `QTrapArray.__init__` now raises `ValueError`
  immediately rather than deferring to the setter
