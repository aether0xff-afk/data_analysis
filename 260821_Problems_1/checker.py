from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_COLUMNS = [
    'sex', 'length', 'diameter', 'height', 'whole_weight',
    'shucked_weight', 'viscera_weight', 'shell_weight', 'rings'
]
NUMERIC_COLS = [
    'length', 'diameter', 'height', 'whole_weight',
    'shucked_weight', 'viscera_weight', 'shell_weight'
]
FIRST_ROW = ['M', 0.455, 0.365, 0.095, 0.514, 0.2245, 0.101, 0.15, 15]


def _ok(label: str, detail: str = '') -> None:
    tail = f' — {detail}' if detail else ''
    print(f'  ✅ {label}{tail}')


def _bad(label: str, detail: str = '') -> None:
    tail = f' — {detail}' if detail else ''
    print(f'  ❌ {label}{tail}')


def _find_code_cell(nb: dict, marker: str) -> str:
    for cell in nb.get('cells', []):
        if cell.get('cell_type') != 'code':
            continue
        src = ''.join(cell.get('source', []))
        if marker in src:
            return src
    return ''


def _get_t5_markdown(nb: dict) -> str:
    for cell in nb.get('cells', []):
        if cell.get('cell_type') != 'markdown':
            continue
        src = ''.join(cell.get('source', []))
        if src.lstrip().startswith('### T5 해석'):
            body = re.sub(r'^\s*###\s*T5\s*해석\s*', '', src, count=1)
            body = body.replace('여기에 2~3문장으로 작성하세요.', '').strip()
            return body
    return ''


def _execute_notebook(nb: dict, notebook_dir: Path):
    ns = {
        '__name__': '__challenge__',
        'display': lambda *args, **kwargs: None,
    }
    errors = []
    old_cwd = Path.cwd()
    try:
        os.chdir(notebook_dir)
        for i, cell in enumerate(nb.get('cells', [])):
            if cell.get('cell_type') != 'code':
                continue
            src = ''.join(cell.get('source', []))
            # 셸 명령 및 체크기 자기호출은 실행하지 않는다.
            if not src.strip() or 'checker.py' in src:
                continue
            if any(line.lstrip().startswith(('!', '%')) for line in src.splitlines()):
                continue
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    exec(compile(src, f'<cell {i}>', 'exec'), ns, ns)
            except Exception as e:
                errors.append((i, type(e).__name__, str(e)))
    finally:
        os.chdir(old_cwd)
    return ns, errors


def _first_row_is_correct(df: pd.DataFrame) -> bool:
    try:
        row = df.iloc[0]
        if str(row['sex']) != FIRST_ROW[0]:
            return False
        for col, expected in zip(EXPECTED_COLUMNS[1:], FIRST_ROW[1:]):
            if not np.isclose(float(row[col]), float(expected), rtol=0, atol=1e-10):
                return False
        return True
    except Exception:
        return False


def _same_rows(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    try:
        # index를 재설정해도 정답으로 인정한다.
        aa = a.reset_index(drop=True)
        bb = b.reset_index(drop=True)
        return list(aa.columns) == list(bb.columns) and aa.equals(bb)
    except Exception:
        return False


def _sentence_count(text: str) -> int:
    clean = re.sub(r'[`*_>#-]', ' ', text)
    pieces = [p.strip() for p in re.split(r'[.!?。]+|\n+', clean) if p.strip()]
    return len(pieces)


def _explanation_reasonable(text: str) -> tuple[bool, str]:
    if not text.strip():
        return False, 'T5 해석 Markdown이 비어 있음'
    n = _sentence_count(text)
    if n < 2 or n > 3:
        return False, f'2~3문장을 권장했지만 현재 약 {n}문장으로 감지됨'

    has_delete = '삭제' in text
    has_caution = any(k in text for k in ['바로', '무조건', '안 ', '않', '아니', '확인', '검증'])
    has_reason = any(k in text for k in [
        '측정', '오류', '실제', '분포', '극단', '표본', '원인', '도메인',
        '데이터', '개체', '관측', '확인', '검증'
    ])
    if has_delete and has_caution and has_reason:
        return True, '이상치=즉시 삭제가 아니라는 판단과 이유가 포함됨'
    return False, '“바로 삭제해도 되는가”에 대한 판단과 근거를 더 분명하게 작성'


def grade(notebook_path: str | Path) -> int:
    notebook_path = Path(notebook_path).resolve()
    if not notebook_path.exists():
        print(f'❌ 노트북을 찾을 수 없습니다: {notebook_path}')
        return 0

    nb = json.loads(notebook_path.read_text(encoding='utf-8'))
    ns, exec_errors = _execute_notebook(nb, notebook_path.parent)

    print('\n' + '=' * 64)
    print('🧪 TODAY DATA PREPROCESSING CHALLENGE — AUTO CHECKER')
    print('=' * 64)
    if exec_errors:
        print(f'⚠️ 실행 중 오류가 난 코드 셀이 {len(exec_errors)}개 있습니다.')
        for idx, typ, msg in exec_errors[:5]:
            print(f'   cell {idx}: {typ}: {msg}')
        print()

    total = 0.0

    # T1 — 2점
    print('[T1] RAW → DataFrame / 2.0')
    df = ns.get('df')
    t1_shape = isinstance(df, pd.DataFrame) and len(df) == 4177 and df.shape[1] >= 9
    t1_cols = isinstance(df, pd.DataFrame) and list(df.columns[:9]) == EXPECTED_COLUMNS
    t1_first = isinstance(df, pd.DataFrame) and _first_row_is_correct(df)
    if t1_shape:
        _ok('기본 데이터 크기', f'4177행 / 기본 9열 + 파생열 {df.shape[1]-9}개')
    else:
        _bad('기본 데이터 크기', getattr(df, 'shape', 'df 없음'))
    if t1_cols:
        _ok('columns')
    else:
        _bad('columns', '지정된 9개 열 이름과 다름')
    if t1_first:
        _ok('첫 데이터 행 보존')
    else:
        _bad('첫 데이터 행 보존', 'header 처리 확인')
    if t1_shape and t1_cols and t1_first:
        total += 2.0
    elif sum([t1_shape, t1_cols, t1_first]) >= 2:
        total += 1.0

    # T2 — 2점
    print('\n[T2] 조건 추출 / 2.0')
    target = ns.get('target')
    t2_ok = False
    if t1_shape and isinstance(target, pd.DataFrame):
        expected_target = df[
            (df['sex'] == 'I') &
            (df['length'] >= 0.5) &
            (df['whole_weight'] >= df['whole_weight'].mean())
        ][EXPECTED_COLUMNS]
        try:
            target_base = target[EXPECTED_COLUMNS]
            t2_ok = _same_rows(target_base, expected_target)
        except Exception:
            t2_ok = False
        if t2_ok:
            _ok('세 조건의 교집합이 정확함', f'{len(target)}행')
        else:
            _bad('target', f'기대 {len(expected_target)}행 / 현재 {len(target)}행')
    else:
        _bad('target', 'DataFrame target이 없거나 T1이 완성되지 않음')
    if t2_ok:
        total += 2.0

    # T3 — 2점
    print('\n[T3] 파생변수 / 2.0')
    t3_source = _find_code_cell(nb, '# TEST T3')
    age_ok = False
    group_value_ok = False
    where_used = 'np.where' in t3_source
    if t1_shape and 'age' in df.columns:
        expected_age = df['rings'].astype(float) + 1.5
        age_ok = np.allclose(df['age'].astype(float).to_numpy(), expected_age.to_numpy(), equal_nan=True)
    if t1_shape and 'age_group' in df.columns and 'age' in df.columns:
        expected_group = np.where(df['age'] >= 12, 'old', 'young')
        group_value_ok = np.array_equal(df['age_group'].astype(str).to_numpy(), expected_group)
    if age_ok:
        _ok('age = rings + 1.5')
        total += 1.0
    else:
        _bad('age')
    if group_value_ok and where_used:
        _ok('age_group 값 + np.where 사용')
        total += 1.0
    else:
        if group_value_ok:
            _bad('np.where 사용', '값은 맞지만 TEST T3 셀에서 np.where를 찾지 못함')
        else:
            _bad('age_group 값')

    # T4 — 2점
    print('\n[T4] NumPy 통계 / 2.0')
    t4_source = _find_code_cell(nb, '# TEST T4')
    has_loop = bool(re.search(r'(^|\n)\s*(for|while)\s+', t4_source))
    x = ns.get('x')
    means = ns.get('means')
    stds = ns.get('stds')
    t4_values = False
    if t1_shape:
        expected_x = df[NUMERIC_COLS].to_numpy()
        expected_means = expected_x.mean(axis=0)
        expected_stds = expected_x.std(axis=0, ddof=1)
        try:
            t4_values = (
                isinstance(x, np.ndarray) and x.shape == (4177, 7) and
                np.allclose(x.astype(float), expected_x.astype(float)) and
                np.asarray(means).shape == (7,) and
                np.asarray(stds).shape == (7,) and
                np.allclose(np.asarray(means, dtype=float), expected_means) and
                np.allclose(np.asarray(stds, dtype=float), expected_stds)
            )
        except Exception:
            t4_values = False
    if t4_values:
        _ok('x / means / stds 값', 'axis=0, ddof=1 결과 일치')
        total += 1.5
    else:
        _bad('x / means / stds 값', '변수 이름도 x, means, stds로 맞춰야 함')
    if not has_loop and t4_source.strip():
        _ok('반복문 미사용')
        total += 0.5
    else:
        _bad('반복문 미사용', 'TEST T4에서는 for/while 없이 벡터 연산 사용')

    # T5 — 2점
    print('\n[T5] height 이상치 + 해석 / 2.0')
    out = ns.get('height_outliers')
    t5_code_ok = False
    if t1_shape and isinstance(out, pd.DataFrame):
        h = df['height'].to_numpy(dtype=float)
        mu = h.mean()
        sigma = h.std(ddof=1)
        expected_out = df[np.abs(df['height'] - mu) > 2 * sigma]
        t5_code_ok = _same_rows(out, expected_out)
        if t5_code_ok:
            _ok('height_outliers', f'{len(out)}행')
            total += 1.0
        else:
            _bad('height_outliers', f'기대 {len(expected_out)}행 / 현재 {len(out)}행')
    else:
        _bad('height_outliers', 'DataFrame 변수가 없음')

    explanation = _get_t5_markdown(nb)
    exp_ok, exp_msg = _explanation_reasonable(explanation)
    if exp_ok:
        _ok('T5 해석', exp_msg)
        total += 1.0
    else:
        _bad('T5 해석', exp_msg)

    total = round(total, 1)
    print('\n' + '-' * 64)
    print(f'점수: {total:.1f} / 10.0')
    if total >= 8.0:
        print('🏁 TODAY CLEAR!')
    else:
        print('🔧 아직 CLEAR 전. ❌ 표시된 항목만 수정해서 다시 실행하세요.')
    print('-' * 64)
    print('※ T5 서술 채점은 간단한 자동 검사입니다. 의미가 애매하면 사람이 다시 볼 수 있습니다.\n')
    return int(total >= 8.0)


def main() -> int:
    if len(sys.argv) >= 2:
        path = Path(sys.argv[1])
    else:
        path = Path('03_TEST_TODAY_CHALLENGE.ipynb')
    try:
        grade(path)
        return 0
    except Exception:
        print('체크기 자체에서 예외가 발생했습니다.')
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
