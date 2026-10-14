# Source publication audit — October 14, 2026

Scope: this source directory and its source-only ZIP, not the private build
workspace or the publisher's policies. The publication checker enforces the
recorded file list and common secret/binary boundaries; it is not a legal or
security guarantee.

- No game/ACE/vendor binaries, account prefixes, credentials, tokens,
  account-bearing logs/screenshots, game icon artwork or copied dependency
  libraries are included. No local user directory is embedded.
- No protected-entry adapter, bootstrap skip, game executable modification,
  CAPTCHA solution, certificate-ignore switch or sandbox-disable switch is
  added. Wine's incomplete virtual kernel is documented, not represented as
  complete anti-cheat enforcement.
- Wine/DW-Proton/MR provenance remains credited. New adaptations and regression
  fixtures from kanata-dp/nikke-crossover-compat are credited at their reviewed
  commit under LGPL-2.1-or-later. Original notices and the LGPL text remain.
- The DXMT implementation is obtained privately from the user's donor. This
  source tree does not modify or submit AI-authored code to the DXMT project.
- The README prominently states the possibility of an account ban and that a
  ban caused by this specific setup has not been confirmed. This does not
  establish permission, account safety or compliance with the game's terms.
- Previous local Git metadata is excluded. A new publisher chooses their own
  commit identity and remote; no repository was created or uploaded here.

Validation: the reviewed module builds, packaged kernel regressions,
GPU/video smoke checks and exact39-file patch verification passed locally.
The user confirmed post-update Launch reaches the lobby.
See TESTING.md for the visual-access/CAPTCHA validation limits. Preserve these limits
and credits in future copies. Publishing and use may still carry licensing,
contractual, security and account-enforcement risks that this audit cannot
rule out.
