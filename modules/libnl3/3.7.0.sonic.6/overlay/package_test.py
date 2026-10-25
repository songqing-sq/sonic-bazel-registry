"""Independent Debian install/control and GNU debug pairing contracts."""
import hashlib
import argparse
import gzip
import io
from pathlib import Path
import re
import sys
import tarfile
import zlib
from elf_metadata import Elf


def contents(path):
    raw = Path(path).read_bytes(); assert raw[:8] == b'!<arch>\n'
    offset = 8; result = {}
    while offset < len(raw):
        header = raw[offset:offset+60]; size = int(header[48:58]); offset += 60
        name = header[:16].decode().strip().rstrip('/')
        result[name] = raw[offset:offset+size]; offset += size + size % 2
    assert list(result) == ['debian-binary', 'control.tar.gz', 'data.tar.gz']
    assert result['debian-binary'] == b'2.0\n'
    archives = []
    for part in ['control.tar.gz', 'data.tar.gz']:
        with tarfile.open(fileobj=io.BytesIO(result[part])) as archive:
            archives.append({entry.name.removeprefix('./'): (entry, archive.extractfile(entry).read() if entry.isfile() else None) for entry in archive})
    return archives


def fields(text):
    out = {}; key = None
    for line in text.splitlines():
        if line.startswith(' ') and key: out[key] += '\n' + line
        elif ': ' in line: key, out[key] = line.split(': ', 1)
    return out


parser = argparse.ArgumentParser()
parser.add_argument('--suite', choices=['bookworm', 'trixie'], required=True)
parser.add_argument('--libc-control', required=True)
parser.add_argument('packages', nargs='+')
args = parser.parse_args()
# Original builder suites are glibc2.36 and glibc2.41. Check selected metadata
# itself as well as target ELF requirements; an exec-side database is incorrect.
expected_glibc = {'bookworm': (2, 36), 'trixie': (2, 41)}[args.suite]
with tarfile.open(args.libc_control) as archive:
    member = next(member for member in archive if member.name.removeprefix('./') == 'control')
    libc = fields(archive.extractfile(member).read().decode())
assert libc['Package'] == 'libc6'
assert libc['Version'].startswith('.'.join(map(str, expected_glibc)) + '-'), libc
packages = {}
for path in args.packages:
    control, data = contents(path)
    metadata = fields(control['control'][1].decode())
    name = metadata['Package']; packages[name] = (metadata, control, data)
    assert metadata['Version'] == '3.7.0-0.2+b1sonic1'
    assert metadata['Architecture'] in ('amd64', 'arm64')
    assert metadata['Architecture'] == libc['Architecture']
    assert metadata['Source'] == 'libnl3'
    assert metadata['Multi-Arch'] == 'same'
    assert int(metadata['Installed-Size']) > 0
    for entry, _ in [*data.values(), *control.values()]:
        assert entry.uid == entry.gid == 0, entry.name
    sums = {}
    for line in control['md5sums'][1].decode().splitlines():
        digest, path = line.split('  ', 1); sums[path] = digest
    conffiles = {line.lstrip('/') for line in control.get('conffiles', (None, b''))[1].decode().splitlines() if line.startswith('/')}
    assert sums == {path: hashlib.md5(payload).hexdigest() for path, (entry, payload) in data.items() if entry.isfile() and path not in conffiles}

families = ['libnl-3', 'libnl-genl-3', 'libnl-route-3', 'libnl-nf-3', 'libnl-cli-3']
assert set(packages) == {stem + suffix for stem in families for suffix in ['-200', '-200-dbgsym', '-dev']}
for stem in families:
    name = stem + '-200'; metadata, control, data = packages[name]
    arch = metadata['Architecture']; triplet = {'amd64': 'x86_64-linux-gnu', 'arm64': 'aarch64-linux-gnu'}[arch]
    libdir = ('lib/' if stem in ['libnl-3', 'libnl-genl-3'] else 'usr/lib/') + triplet
    library = libdir + '/' + stem + '.so.200.26.0'
    assert library in data, (name, library)
    assert data[libdir + '/' + stem + '.so.200'][0].linkname == stem + '.so.200.26.0'
    elf = Elf(data[library][1]); assert elf.soname == stem + '.so.200'
    assert elf.machine == {'amd64': 62, 'arm64': 183}[arch]
    assert control['triggers'][1] == b'activate-noawait ldconfig\n'
    assert control['shlibs'][1].decode() == stem + ' 200 ' + name + ' (>= 3.7.0)\n'
    symbols = control['symbols'][1].decode()
    for symbol, version in elf.export_versions:
        assert '\n ' + symbol + '@' + (version or 'Base') + ' ' in symbols, symbol
    assert metadata['Depends'].count('libc6') == 1, metadata['Depends']
    for need in elf.needed:
        if need.startswith('libnl'):
            package = need.split('.so.')[0] + '-200'
            assert package in metadata['Depends'], (name, need)
    debug_metadata, debug_control, debug_data = packages[name + '-dbgsym']
    expected_ids = []
    for path, (entry, payload) in data.items():
        if payload and payload.startswith(b'\x7fELF'):
            runtime_elf = Elf(payload); build_id = runtime_elf.build_id
            for dependency, version in runtime_elf.required_versions:
                if dependency == 'libc.so.6' and re.fullmatch(r'GLIBC_[0-9]+(?:\.[0-9]+)*', version):
                    assert tuple(map(int, version[6:].split('.'))) <= expected_glibc, (path, version, args.suite)
            assert build_id and runtime_elf.debuglink
            debug_path = 'usr/lib/debug/.build-id/' + build_id[:2] + '/' + build_id[2:] + '.debug'
            debug_payload = debug_data[debug_path][1]
            assert Elf(debug_payload).build_id == build_id
            assert zlib.crc32(debug_payload) == runtime_elf.debuglink_crc
            expected_ids.append(build_id)
    assert debug_metadata['Build-Ids'].split() == sorted(set(expected_ids))
    assert debug_data['usr/share/doc/' + name + '-dbgsym'][0].linkname == name
    assert debug_metadata['Depends'] == name + ' (= 3.7.0-0.2+b1sonic1)'
    assert debug_metadata['Auto-Built-Package'] == 'debug-symbols'
    assert hashlib.sha256(gzip.decompress(data['usr/share/doc/' + name + '/changelog.gz'][1])).hexdigest() == 'dae6079d90fdf3facdcce8f9bcc316dcfd1a7dae855d79428e5f0937f6dda628'
    assert hashlib.sha256(data['usr/share/doc/' + name + '/copyright'][1]).hexdigest() == '9a3730df4bb18c8be5fdce05b9223f9b152b6bf40f7e45319529830ecd413eb2'
    dev_metadata, dev_control, dev_data = packages[stem + '-dev']
    assert name + ' (= 3.7.0-0.2+b1sonic1)' in dev_metadata['Depends']
    assert dev_data[libdir + '/' + stem + '.a'][1].startswith(b'!<arch>\n')
    assert dev_data[libdir + '/' + stem + '.so'][0].linkname == stem + '.so.200'
    assert not any(path.endswith('.so.200.26.0') for path in dev_data)
    assert 'usr/lib/' + triplet + '/pkgconfig/' + stem + '.0.pc' in dev_data
    if stem == 'libnl-3':
        assert control['conffiles'][1] == b'/etc/libnl-3/classid\n/etc/libnl-3/pktloc\n'
        assert 'etc/libnl-3/classid' in data and 'etc/libnl-3/pktloc' in data
        assert hashlib.sha256(data['usr/share/doc/' + name + '/README.Debian'][1]).hexdigest() == '8d12a518903884cd8ae65844d99e1d5401a3ed8a6256006234baf0583e3cca94'
        assert 'usr/include/libnl3/netlink/netlink.h' in dev_data
        assert dev_metadata['Conflicts'] == 'libnl-dev, libnl2-dev'
        assert dev_metadata['Breaks'] == dev_metadata['Replaces'] == 'libnl3-dev'
    if stem == 'libnl-cli-3':
        # Exact plugin set in upstream Makefile.am and Debian wildcard manifests.
        plugins = ['cls/basic', 'cls/cgroup', 'qdisc/bfifo', 'qdisc/blackhole', 'qdisc/fq_codel', 'qdisc/hfsc', 'qdisc/htb', 'qdisc/ingress', 'qdisc/pfifo', 'qdisc/plug']
        for plugin in plugins:
            assert 'usr/lib/' + triplet + '/libnl-3/cli/' + plugin + '.so' in data
            assert dev_data['usr/lib/' + triplet + '/libnl/cli/' + plugin + '.a'][1].startswith(b'!<arch>\n')
print('15 Debian package contracts and GNU debug pairs passed')
