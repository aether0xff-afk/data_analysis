from pathlib import Path
from urllib.request import urlopen, Request
import io
import zipfile

URL = "https://archive.ics.uci.edu/static/public/1/abalone.zip"
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)

print("Downloading official UCI Abalone archive...")
req = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urlopen(req, timeout=30) as r:
    content = r.read()

with zipfile.ZipFile(io.BytesIO(content)) as zf:
    wanted = {"abalone.data", "abalone.names", "Index"}
    for name in zf.namelist():
        base = Path(name).name
        if base in wanted:
            target = OUT / base
            target.write_bytes(zf.read(name))
            print("saved:", target.relative_to(Path(__file__).resolve().parent))

if not (OUT / "abalone.data").exists():
    raise RuntimeError("abalone.data was not found in the downloaded archive.")

print("Done. Open 01_LEARN_A_RAW_TO_DF.ipynb")
