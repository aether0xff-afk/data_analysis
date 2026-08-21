from pathlib import Path
from urllib.request import Request, urlopen
import pandas as pd
import numpy as np
import io

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Public mirror of UCI Air Quality data. Source attribution remains UCI.
URL = "https://raw.githubusercontent.com/PacktPublishing/Time-Series-Analysis-with-Python-Cookbook-Second-Edition/refs/heads/main/datasets/Ch1/AirQualityUCI.csv"

EXPECTED = [
    "Date","Time","CO(GT)","PT08.S1(CO)","NMHC(GT)","C6H6(GT)",
    "PT08.S2(NMHC)","NOx(GT)","PT08.S3(NOx)","NO2(GT)",
    "PT08.S4(NO2)","PT08.S5(O3)","T","RH","AH"
]

def download_base():
    print("[1/3] Downloading AirQualityUCI.csv ...")
    req = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as r:
        raw = r.read()

    # The mirror is semicolon-separated.
    df = pd.read_csv(io.BytesIO(raw), sep=";")
    df.columns = df.columns.str.strip()

    missing = [c for c in EXPECTED if c not in df.columns]
    if missing:
        raise RuntimeError(f"Unexpected source format. Missing columns: {missing}")
    if len(df) < 9000:
        raise RuntimeError(f"Unexpected source size: {len(df)} rows")

    df = df[EXPECTED].copy()
    out = DATA_DIR / "AirQualityUCI_BASE.csv"
    df.to_csv(out, index=False, sep=";")
    print(f"    saved: {out.name} ({len(df):,} rows)")
    return df

def dirtyify(part, seed):
    rng = np.random.default_rng(seed)
    df = part.copy().reset_index(drop=True)

    # 1) Header whitespace
    rename = {}
    for i, c in enumerate(df.columns):
        if i % 3 == 0:
            rename[c] = f" {c} "
        elif i % 5 == 0:
            rename[c] = f"{c} "
    df = df.rename(columns=rename)

    # Strip only for internal column addressing while injecting corruption.
    lookup = {c.strip(): c for c in df.columns}

    # 2) Date/time whitespace
    for col in ["Date", "Time"]:
        real = lookup[col]
        picks = rng.choice(df.index, size=min(35, len(df)), replace=False)
        df[real] = df[real].astype(str)
        df.loc[picks, real] = "  " + df.loc[picks, real].astype(str) + " "

    # 3) Invalid date tokens
    dcol = lookup["Date"]
    bad_dates = rng.choice(df.index, size=min(4, len(df)), replace=False)
    bad_tokens = ["31/02/2004", "not-a-date", "99/99/9999", ""]
    for idx, token in zip(bad_dates, bad_tokens):
        df.loc[idx, dcol] = token

    # 4) Numeric string corruption
    corrupt_cols = ["CO(GT)", "NOx(GT)", "NO2(GT)", "T", "RH", "PT08.S1(CO)"]
    tokens = ["?", "NA", "error"]
    for name in corrupt_cols:
        col = lookup[name]
        df[col] = df[col].astype(object)
        picks = rng.choice(df.index, size=min(12, len(df)), replace=False)
        for j, idx in enumerate(picks):
            if j < 9:
                df.loc[idx, col] = tokens[j % len(tokens)]
            else:
                # Valid numeric value, but as a padded string.
                df.loc[idx, col] = f"  {df.loc[idx, col]}  "

    # 5) Fully empty junk column
    df[" Unnamed: 99 "] = np.nan

    # 6) Duplicate rows
    dup_idx = rng.choice(df.index, size=min(18, len(df)), replace=False)
    df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)

    # 7) Shuffle ordering
    order = rng.permutation(len(df))
    df = df.iloc[order].reset_index(drop=True)

    return df

def main():
    base = download_base()

    # Time-disjoint learn/test sections.
    learn_base = base.iloc[:5600].copy()
    test_base = base.iloc[5600:].copy()

    learn = dirtyify(learn_base, seed=20260821)
    test = dirtyify(test_base, seed=20260822)

    learn_path = DATA_DIR / "AirQuality_DIRTY_LEARN.csv"
    test_path = DATA_DIR / "AirQuality_DIRTY_TEST.csv"

    learn.to_csv(learn_path, index=False, sep=";")
    test.to_csv(test_path, index=False, sep=";")

    print(f"[2/3] created: {learn_path.name} ({len(learn):,} rows)")
    print(f"[3/3] created: {test_path.name} ({len(test):,} rows)")
    print("\nREADY. Open 01_LEARN_A_STRUCTURE_AND_TYPES.ipynb")

if __name__ == "__main__":
    main()
