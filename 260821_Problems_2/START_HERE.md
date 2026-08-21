# 🧹 ADVANCED DIRTY DATA CHALLENGE — UCI Air Quality

오늘의 구조는 그대로입니다.

> **LEARN A → LEARN B → TEST → AUTO CHECK**

이번에는 깨끗한 예제 데이터가 아닙니다.  
UCI **Air Quality** 데이터를 기반으로, 실제 원본의 문제점(`-200` 결측 표식, 날짜/시간 문자열)에
교육용 오염을 추가하여 만든 **재현 가능한 DIRTY 데이터**를 사용합니다.

## 0. 준비

터미널에서 이 폴더로 이동한 뒤:

```bash
pip install -r requirements.txt
python setup_data.py
```

성공하면 `data/` 안에 다음 파일이 생깁니다.

- `AirQualityUCI_BASE.csv` : 다운로드한 기준 데이터
- `AirQuality_DIRTY_LEARN.csv` : 학습 미션용
- `AirQuality_DIRTY_TEST.csv` : 최종 테스트용

> 네트워크가 필요한 건 `setup_data.py`를 처음 실행할 때뿐입니다.

---

## 1. 학습 미션 A

`01_LEARN_A_STRUCTURE_AND_TYPES.ipynb`

새로 배우는 것:

- `sep=';'`
- `df.info()`
- `df.columns.str.strip()`
- `dropna(axis=1, how='all')`
- `replace()`
- `pd.to_numeric(errors='coerce')`
- `isna().sum()`

목표: **"파일은 읽혔는데 데이터 타입과 결측 표현이 엉망"인 상태를 구조적으로 복구**

---

## 2. 학습 미션 B

`02_LEARN_B_TIME_AND_MISSING.ipynb`

새로 배우는 것:

- 문자열 정리 `.str.strip()`
- `pd.to_datetime(..., errors='coerce')`
- `sort_values()`
- `drop_duplicates()`
- `interpolate()`
- 결측값을 열의 의미에 따라 다르게 처리하는 판단
- `np.where`
- 벡터화한 파생 변수

목표: **시계열 데이터로 사용할 수 있는 상태까지 정리**

---

## 3. 최종 테스트

`03_TEST_DIRTY_PIPELINE.ipynb`

테스트에는 정답 코드가 없습니다.

해야 할 일:

1. `data/AirQuality_DIRTY_TEST.csv` 읽기
2. 열 이름/빈 열 정리
3. 날짜+시간 → `datetime`
4. 잘못된 datetime 제거
5. 중복 행/시간 제거
6. 숫자형 열 변환
7. `-200`, `?`, `NA`, `error` 등을 결측치로 처리
8. 센서/기상 데이터만 시간 순서로 보간
9. 파생 변수 3개 생성
10. `submission.csv` 저장

마지막 셀에서 자동 채점:

```python
%run checker.py
check_submission("submission.csv")
```

또는 터미널:

```bash
python checker.py submission.csv
```

## 점수

- 10/10 : **ADVANCED CLEAR**
- 8~9 : 통과, 감점 항목 확인
- 7 이하 : 해당 항목을 고치고 재도전

## 중요한 규칙

- 테스트에서 `for` / `while`을 이용해 행 하나씩 처리하지 마세요.
- 숫자 변환 실패를 숨기려고 모든 행을 통째로 삭제하면 안 됩니다.
- 모든 결측치를 같은 방식으로 채우지 마세요.
- `-200`은 실제 측정값이 아니라 UCI에서 사용한 missing-value marker입니다.
