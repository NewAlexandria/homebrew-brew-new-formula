# typed: false
# frozen_string_literal: true

class BrewNewFormulae < Formula
  desc "List formulae and casks added to Homebrew taps within a date range"
  homepage "https://github.com/newalexandria/homebrew-brew-new-formula"
  url "https://github.com/newalexandria/homebrew-brew-new-formula/archive/refs/tags/v1.0.0.tar.gz"
  version "1.0.0"
  sha256 "8ee3a9b74b8e3c38b94f364a0b0e4a66f9097e4f3e2f4020d8d8918c78323847"
  head "https://github.com/newalexandria/homebrew-brew-new-formula.git", branch: "main"
  license "MIT"

  depends_on "python@3.12"

  def install
    libexec.install "lib/brew_new_formulae.py", "lib/brew_first_installs.py", "lib/brew_index.py"
    python = Formula["python@3.12"].opt_bin/"python3.12"

    (bin/"brew-new-formulae").write <<~EOS
      #!/bin/bash
      exec "#{python}" "#{opt_libexec}/brew_new_formulae.py" "$@"
    EOS
    (bin/"brew-first-installs").write <<~EOS
      #!/bin/bash
      exec "#{python}" "#{opt_libexec}/brew_first_installs.py" "$@"
    EOS
    (bin/"brew-rebuild-index").write <<~EOS
      #!/bin/bash
      exec "#{python}" "#{opt_libexec}/brew_index.py" "$@"
    EOS

    [bin/"brew-new-formulae", bin/"brew-first-installs", bin/"brew-rebuild-index"].each { |f| chmod 0755, f }
  end

  test do
    # brew new-formulae requires two integer args; --help exits 0
    system bin/"brew-new-formulae", "--help"
    # Should run without error (may produce empty output)
    system bin/"brew-new-formulae", "0", "7"
    # Use a writable dir for the index (Cellar/opt/homebrew is read-only in CI)
    ENV["BREW_NEW_FORMULAE_INDEX_DIR"] = Dir.mktmpdir
    system bin/"brew-rebuild-index"
  end
end
