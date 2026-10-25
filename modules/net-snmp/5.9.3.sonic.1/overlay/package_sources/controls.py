"""Expand original maintainer scripts using declared debhelper templates."""
import json
from pathlib import Path
import re
import subprocess
import argparse
from python.runfiles import runfiles
import tarfile
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source-marker', required=True)
parser.add_argument('--mapping', required=True, type=json.loads)
parser.add_argument('--conffiles', required=True, type=json.loads)
parser.add_argument('--shlibs', required=True)
parser.add_argument('--debhelper-data', required=True)
parser.add_argument('--package', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()
request = vars(args)
request['source_root'] = str(Path(args.source_marker).parent)
request['outputs'] = {args.package: args.output}
request['debhelper_data'] = args.debhelper_data
request['po2debconf'] = runfiles.Create().Rlocation('sonic_build_infra/tools/build_tools/po2debconf')
source = Path(request['source_root'])
mapping = request['mapping']
with tarfile.open(request['debhelper_data']) as archive:
    snippets = {m.name.rsplit('/', 1)[-1]: archive.extractfile(m).read().decode() for m in archive if m.isfile() and '/debhelper/autoscripts/' in m.name}
for package, output in request['outputs'].items():
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    for kind in ['preinst', 'postinst', 'prerm', 'postrm', 'config']:
        original = source / 'debian' / (package + '.' + kind)
        entries = mapping.get(package, {}).get(kind, [])
        if not original.is_file() and not entries:
            continue
        text = original.read_text() if original.is_file() else '#!/bin/sh\nset -e\n#DEBHELPER#\n'
        chunks = []
        for entry in entries:
            body = snippets[entry['template']]
            for key, value in entry['substitutions'].items():
                body = body.replace('#' + key + '#', value)
            if re.search(r'#[A-Z_]+#', body):
                raise ValueError('Unexpanded autoscript token: ' + entry['template'])
            helper = 'dh_installdebconf' if entry['template'] == 'postrm-debconf' else ('dh_installsystemd' if '-systemd' in entry['template'] else 'dh_installinit')
            chunks.append('# Automatically added by ' + helper + '/13.11.4\n' + body + '# End automatically added section\n')
        text = text.replace('#DEBHELPER#', ''.join(chunks).rstrip('\n'))
        target = directory / kind
        target.write_text(text)
        target.chmod(0o755)
    if package == 'snmpd':
        # po2debconf may add/remove a synthetic no.po beside the inputs.
        # Keep that directory private and link its immutable declared files.
        with tempfile.TemporaryDirectory() as temporary:
            staging = Path(temporary) / 'debian'
            staging.mkdir()
            podir = staging / 'po'
            podir.mkdir()
            for path in (source / 'debian/po').iterdir():
                (podir / path.name).symlink_to(path.absolute())
            (staging / 'snmpd.templates').symlink_to((source / 'debian/snmpd.templates').absolute())
            result = subprocess.run([str(Path(request['po2debconf']).absolute()), str(staging / 'snmpd.templates')], check=True, stdout=subprocess.PIPE)
        (directory / 'templates').write_bytes(result.stdout)
        (directory / 'templates').chmod(0o644)

    conffiles = request['conffiles'].get(package, [])
    if conffiles:
        (directory / 'conffiles').write_text('\n'.join(conffiles) + '\n')
    if package in ['libsnmp40', 'libnetsnmptrapd40']:
        lines = [line for line in Path(request['shlibs']).read_text().splitlines() if line.split()[2] == package]
        (directory / 'shlibs').write_text('\n'.join(lines) + '\n')
        (directory / 'triggers').write_text('activate-noawait ldconfig\n')
