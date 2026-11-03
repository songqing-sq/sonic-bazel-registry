# Shared migration infrastructure

This version pins source commit `704604e78f8e9f21e1e10143b668786830b52a97` on the maintained
upstream baseline `34de7330abc72229dfc8dab88dec71b89c52aa88`.
It preserves the shared APT lock and library interfaces, Python installation and
runtime dependency metadata, source preparation, declared execution tools,
Autoconf probes, compiler variants, pkg-config exports, Debian metadata,
installation RPATH and detached debug symbols alongside the upstream native
Bookworm/Trixie interfaces.

The registry consumer uses the checksum-checked source archive, version patch
and validation-only overlay without a source override. Its configuration declares
native AMD64 and ARM64 CI jobs. This local baseline validates native AMD64 and
ARM64 cross-builds.

The source archive is prepared locally and remains unpublished. Before publishing,
verify the GitHub archive URL and integrity against the released source commit.
