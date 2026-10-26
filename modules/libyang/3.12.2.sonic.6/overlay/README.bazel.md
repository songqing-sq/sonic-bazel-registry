# libyang native library, tools and Debian packages

This module builds libyang 3.12.2-1 with the SONiC validation extension.
Public targets are `libyang` (CcInfo), interactive `yanglint`, `yangre`,
`libyang_pkg`, `development_pkg`, `tools_pkg` and paired `.debug_symbols` targets.
The `runtime_deb`, `development_deb`, `tools_deb`, `runtime_dbg_deb` and
`tools_dbg_deb` targets use shared `sonic_deb` rules and native ELF dependency metadata.

The development package includes public headers, pkg-config metadata, the linker
symlink and HTML documentation. Declared Doxygen and Graphviz tools generate HTML
from the upstream Doxyfile, headers and plugin sources. Documentation is included
in the default package. The tools package includes man pages and examples.
Man pages and changelogs use the declared gzip toolchain. PCRE2 and xxHash use
target Debian shared libraries selected for Trixie or Bookworm.

`runtime_packages.json` exports package identity for Trixie image consumers.
`source_snapshot` includes source files and generated headers for source delivery.

`libyang_package_test` checks installed payloads and debug symbol pairing using
stdlib ELF inspection. `libyang_test` covers schema/data parsing and the SONiC
validation extension through the declared target loader and runtime libraries.

`upstream_check` runs 56 CMocka programs, the compatibility-header check, three
fuzz-regression drivers, and interactive/noninteractive yanglint and yangre Tcl
suites. `upstream_test_binaries` builds the test executables, two plugins and C
compatibility source for cross-build verification. The Tcl suites use child
interpreters; the runner checks their Total/Passed/Skipped/Failed results and
command exit status. Interactive tests receive a controlling terminal.
