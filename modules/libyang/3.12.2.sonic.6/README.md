# libyang 3.12.2.sonic.6

Native Bazel C rules build the SONiC-patched libyang 3.12.2 library, interactive yanglint and yangre. Target PCRE2 and xxHash shared libraries use fixed Debian APT snapshots selected for Trixie or Bookworm. The public interface provides SONAME libyang.so.3, installed headers and pkg-config metadata.

The module builds five Debian packages: libyang3, libyang-dev, libyang3-tools and their two debug packages. Shared sonic_deb rules provide packaging, dependency metadata and debug information. The development package includes HTML documentation generated with declared Doxygen and Graphviz tools. AMD64 and ARM64 package layouts and suite-specific compiler flags are declared in BUILD.bazel.
