# The page: index.html with the manifest and game.js inlined; the pictures stay as files in assets/ (published next
# to the page). With --single, every picture is put into the page too (base64), for a one-file copy.
import base64, json, pathlib, sys
root = pathlib.Path('/home/claude/runner_hd')
html = (root / 'index.html').read_text()
js = (root / 'game.js').read_text()
snd = (root / 'sound.js').read_text()
stg = (root / 'stages.js').read_text()
man = json.loads((root / 'assets/manifest.json').read_text())
single = '--single' in sys.argv
if single:
    files = {p.name: base64.b64encode(p.read_bytes()).decode() for p in sorted((root / 'assets').glob('*.webp'))}
    data = 'window.__ASSETS=' + json.dumps({'manifest': man, 'files': files}, separators=(',', ':')) + ';'
else:
    data = 'window.__MANIFEST=' + json.dumps(man, separators=(',', ':')) + ';'
assert '</script' not in js and '</script' not in data and '</script' not in snd and '</script' not in stg
html = html.replace('<script src="sound.js"></script>', '<script>\n' + snd + '\n</script>')
html = html.replace('<script src="stages.js"></script>', '<script>\n' + stg + '\n</script>')
html = html.replace('<script src="game.js"></script>', '<script>\n' + data + '\n</script>\n<script>\n' + js + '\n</script>')
out = root / ('artifact_single.html' if single else 'artifact.html')
out.write_text(html)
print(out.name, len(html))
