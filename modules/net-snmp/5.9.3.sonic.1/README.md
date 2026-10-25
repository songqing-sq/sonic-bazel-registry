Native Bazel Net-SNMP 5.9.3 for SONiC Bookworm.

The source rule applies pinned Debian and SONiC patches. Native rules build
libraries, applications, Perl XS bindings, documentation and Debian packages.
BUILD.bazel declares configuration and installation data; template actions
produce the required headers and installed compatibility interfaces.

The patched source repository consumes `source.BUILD.bazel` directly. Its
libraries export complete and headers-only interfaces; the Perl XS source
headers declare their own include directories. Static installation files and
tar composition use `rules_pkg`; Debian metadata is passed to `sonic_deb`.
The resource helpers implement Net-SNMP manpage, documentation, maintainer
script, and Perl compatibility transformations. XS and PM input directory views
use declared symbolic links. The PO directory stays private for po2debconf temporary siblings; its immutable
PO files and template are symlinked. Pkg-config output groups reuse the declared
expanded templates directly.
