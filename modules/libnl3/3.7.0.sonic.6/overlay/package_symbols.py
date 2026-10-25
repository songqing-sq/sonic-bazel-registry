"""Project the actual libnl dynamic exports into Debian symbols metadata."""
import argparse
from pathlib import Path
import tarfile
from elf_metadata import Elf


def main():
    parser = argparse.ArgumentParser()
    for name in ["archive", "reference", "stem", "package", "version", "output"]:
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    reference = {}
    for line in Path(args.reference).read_text().splitlines():
        if line.startswith(" "):
            fields = line.split()
            if len(fields) >= 2:
                reference[fields[0]] = fields[1]
    symbols = []
    with tarfile.open(args.archive) as archive:
        for member in archive:
            if not member.isfile():
                continue
            payload = archive.extractfile(member).read()
            if not payload.startswith(b"\x7fELF"):
                continue
            elf = Elf(payload)
            if elf.soname == args.stem + ".so.200":
                for name, version in sorted(elf.export_versions, key=lambda value: (value[0], value[1] or "")):
                    symbol = name + "@" + (version or "Base")
                    symbols.append(" " + symbol + " " + reference.get(symbol, args.version))
    Path(args.output).write_text(args.stem + ".so.200 " + args.package + " #MINVER#\n" + "\n".join(symbols) + "\n")


if __name__ == "__main__":
    main()
