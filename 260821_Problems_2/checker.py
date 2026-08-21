from pathlib import Path
import sys
import json
import ast
import numpy as np
import pandas as pd

EXPECTED_COLS = [
    'datetime',
    'CO(GT)', 'PT08.S1(CO)', 'NMHC(GT)', 'C6H6(GT)',
    'PT08.S2(NMHC)', 'NOx(GT)', 'PT08.S3(NOx)', 'NO2(GT)',
    'PT08.S4(NO2)', 'PT08.S5(O3)', 'T', 'RH', 'AH',
    'sensor_mean', 'is_rush_hour', 'temp_z'
]
NUMERIC_COLS = EXPECTED_COLS[1:14]
GT_COLS = ['CO(GT)', 'NMHC(GT)', 'C6H6(GT)', 'NOx(GT)', 'NO2(GT)']
CONT_COLS = [
    'PT08.S1(CO)', 'PT08.S2(NMHC)', 'PT08.S3(NOx)',
    'PT08.S4(NO2)', 'PT08.S5(O3)', 'T', 'RH', 'AH'
]
SENSOR_COLS = [
    'PT08.S1(CO)', 'PT08.S2(NMHC)', 'PT08.S3(NOx)',
    'PT08.S4(NO2)', 'PT08.S5(O3)'
]

def notebook_source(path):
    if not path:
        return ""
    p = Path(path)
    if not p.exists():
        return ""
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        return "\n".join(
            "".join(c.get("source", []))
            for c in obj.get("cells", [])
            if c.get("cell_type") == "code"
        )
    except Exception:
        return ""

def result(ok, pts, label, detail=""):
    mark = "✅" if ok else "❌"
    gained = pts if ok else 0
    print(f"{mark} {label}: {gained}/{pts}" + (f" — {detail}" if detail else ""))
    return gained

def check_submission(path="submission.csv", notebook_path=None):
    path = Path(path)
    print("=" * 64)
    print("ADVANCED DIRTY DATA — AUTO CHECKER")
    print("=" * 64)

    if not path.exists():
        print(f"❌ {path} 파일이 없습니다. T6에서 저장했는지 확인하세요.")
        return 0

    try:
        df = pd.read_csv(path)
    except Exception as e:
        print("❌ submission.csv를 읽을 수 없습니다:", e)
        return 0

    score = 0

    # 1) schema
    ok = list(df.columns) == EXPECTED_COLS
    score += result(ok, 1, "1. 제출 열/순서", f"현재 {len(df.columns)} columns")

    # datetime parse
    dt = pd.to_datetime(df.get("datetime"), errors="coerce") if "datetime" in df else pd.Series(dtype="datetime64[ns]")
    ok = len(df) > 3000 and dt.notna().all()
    score += result(ok, 1, "2. datetime 변환/유효 행", f"rows={len(df):,}, invalid={int(dt.isna().sum()) if len(dt) else 'N/A'}")

    ok = len(dt) == len(df) and dt.is_monotonic_increasing and dt.is_unique
    score += result(ok, 1, "3. 시간 정렬 + timestamp 중복 제거")

    # numeric types and bad tokens/-200
    numeric_ok = all(c in df and pd.api.types.is_numeric_dtype(df[c]) for c in NUMERIC_COLS)
    sentinel_left = False
    if numeric_ok:
        sentinel_left = any((df[c] == -200).any() for c in NUMERIC_COLS)
    ok = numeric_ok and not sentinel_left
    score += result(ok, 1, "4. numeric dtype + -200 제거")

    # continuous columns should be fully imputed
    ok = all(c in df for c in CONT_COLS) and df[CONT_COLS].isna().sum().sum() == 0
    score += result(ok, 1, "5. 센서/기상 결측 보간",
                    f"remaining={int(df[CONT_COLS].isna().sum().sum()) if all(c in df for c in CONT_COLS) else 'N/A'}")

    # GT should NOT be completely imputed; expected to retain missingness
    if all(c in df for c in GT_COLS):
        gt_missing = int(df[GT_COLS].isna().sum().sum())
        ok = gt_missing > 0
    else:
        gt_missing, ok = 0, False
    score += result(ok, 1, "6. Ground Truth 결측 보존", f"GT NaN={gt_missing}")

    # sensor_mean
    if all(c in df for c in SENSOR_COLS + ["sensor_mean"]):
        expected = df[SENSOR_COLS].mean(axis=1)
        ok = np.allclose(df["sensor_mean"], expected, rtol=1e-10, atol=1e-10, equal_nan=True)
    else:
        ok = False
    score += result(ok, 1, "7. sensor_mean")

    # rush hour
    if len(dt) == len(df) and "is_rush_hour" in df:
        hours = dt.dt.hour
        expected = np.where(((hours >= 7) & (hours <= 9)) | ((hours >= 17) & (hours <= 19)), 1, 0)
        vals = pd.to_numeric(df["is_rush_hour"], errors="coerce").to_numpy()
        ok = np.array_equal(vals, expected)
    else:
        ok = False
    score += result(ok, 1, "8. is_rush_hour")

    # temp_z ddof=0
    if "T" in df and "temp_z" in df and df["T"].notna().all():
        expected = (df["T"] - df["T"].mean()) / df["T"].std(ddof=0)
        ok = np.allclose(df["temp_z"], expected, rtol=1e-7, atol=1e-7)
    else:
        ok = False
    score += result(ok, 1, "9. temp_z (ddof=0)")

    # technique source scan, soft-but-scored
    src = notebook_source(notebook_path)
    if src:
        used_np_where = "np.where" in src
        try:
            tree = ast.parse(src)
            has_row_loop = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
        except SyntaxError:
            # IPython magics can make the concatenated source unparsable.
            cleaned = "\n".join(line for line in src.splitlines() if not line.lstrip().startswith("%"))
            try:
                tree = ast.parse(cleaned)
                has_row_loop = any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree))
            except SyntaxError:
                has_row_loop = False
        ok = used_np_where and not has_row_loop
        detail = f"np.where={'YES' if used_np_where else 'NO'}, row-loop={'YES' if has_row_loop else 'NO'}"
    else:
        # CLI without notebook_path: don't punish source-inspection-specific rule.
        ok, detail = True, "notebook source check skipped"
    score += result(ok, 1, "10. 벡터화 규칙", detail)

    print("-" * 64)
    print(f"TOTAL: {score}/10")
    if score == 10:
        print("🏆 ADVANCED CLEAR — 데이터 파이프라인 통과")
    elif score >= 8:
        print("✅ CLEAR — 감점 항목만 다시 확인")
    else:
        print("🔧 RETRY — ❌ 항목을 수정하고 다시 실행")
    print("=" * 64)
    return score

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) >= 2 else "submission.csv"
    nb = sys.argv[2] if len(sys.argv) >= 3 else None
    check_submission(target, notebook_path=nb)
