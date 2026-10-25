# libnl3 3.7.0 native Bazel overlay

`libnl_3`, `libnl_genl_3`, `libnl_route_3`, `libnl_nf_3` and `libnl_cli_3` expose CcInfo interfaces. `all_libraries` builds all seven library families, including idiag and xfrm. `programs` builds 47 CLI programs; `check_programs` builds 27 test programs. The optional libcheck tests are disabled.

`debs` builds fifteen packages: five runtime libraries, five development packages and five debug packages. Individual package targets are `<binary-package>_deb`. Staging preserves Debian install splits, static archives, CLI modules, notices, version-equal dependencies, symbol-version metadata, ldconfig triggers and conffiles. The shared `sonic_deb` rule assembles packages; `sonic_shlibdeps` calculates dependencies from declared target ELF and symbol metadata.

Configuration headers and pkg-config metadata use native template expansion. Flex/Bison actions use declared execution tools. `source_snapshot` includes library source and generated headers and parsers.

`native_package_test` and `libnl3_package_test` inspect artifacts using execution-side Python. `libnl3_consumer_test` runs when execution and target CPUs match, using declared libc6 and source-built libraries. Cross compilation validates artifacts without executing target ELF. Both Debian Bookworm and Trixie target platforms are supported.
