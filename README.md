# brew-new-formulae

Homebrew external commands to discover new formulae and track first installs.

## Commands

- **`brew new-formulae <days_ago> <days_ago>`** — List formulae and casks added to Homebrew taps within a date range. Uses the same tap git history that powers `brew update`'s "New Formulae". Run `brew update` first for accuracy.

- **`brew first-installs <days_ago> <days_ago>`** — Find packages whose first-installed date falls within a range. Uses an index of your Cellar/Caskroom.

- **`brew rebuild-index`** — Rebuild the installs index (used by `brew first-installs` when the index is missing or stale).

## Installation

### Option 1: Formula (recommended)

```bash
brew tap newalexandria/brew-new-formula
brew install newalexandria/brew-new-formula/brew-new-formulae
```

### Option 2: Tap only (no formula install)

```bash
brew tap newalexandria/brew-new-formula
```

The commands are available immediately after tapping. Scripts run from the tap directory.

## Examples

```bash
# New formulae added in the last 30 days
brew new-formulae 0 30

# New formulae with description and URL (like brew update)
brew new-formulae 0 7 --brew-style

# Packages first installed in the last 30 days
brew first-installs 0 30

# Rebuild the installs index
brew rebuild-index
```

## Requirements

- Homebrew
- Python 3.12+
- Git (for tap scanning)

## License

MIT
