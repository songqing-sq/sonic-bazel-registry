"""Bind Net-SNMP Perl XS dependencies to the declared target Perl package."""
from pathlib import Path
import re
import sys
import tarfile

control, shlibs, output = sys.argv[1:]
with tarfile.open(control) as archive:
    member = next(item for item in archive if item.name.removeprefix("./") == "control")
    fields = archive.extractfile(member).read().decode()
version = re.search(r"^Version: (.+)$", fields, re.M).group(1)
dependencies = ["perl (>= " + version + ")", "perlapi-5.36.0"]
if Path(shlibs).read_text().strip():
    dependencies.append(Path(shlibs).read_text().strip())
Path(output).write_text(", ".join(dependencies) + "\n")
