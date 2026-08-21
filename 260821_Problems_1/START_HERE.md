# 오늘의 데이터 전처리 챌린지 — UCI Abalone

## 오늘의 규칙
오늘은 **학습 미션 2개 + 테스트 1개**만 합니다.

1. `01_LEARN_A_RAW_TO_DF.ipynb` — RAW 파일 → DataFrame
2. `02_LEARN_B_FILTER_AND_NUMPY.ipynb` — 조건 추출 + 파생변수 + NumPy 통계
3. `03_TEST_TODAY_CHALLENGE.ipynb` — 힌트 없이 종합 테스트
4. `checker.py` — 저장된 테스트 답안을 자동 채점

### 통과 기준
- 학습 미션 A/B: 모든 TODO 셀이 정상 실행되면 통과
- 테스트: **10점 만점 중 8점 이상**이면 오늘 챌린지 CLEAR
- 테스트에서는 학습 미션에 나오지 않은 새 문법을 요구하지 않습니다.

## 준비
Python 패키지:

```bash
pip install numpy pandas jupyter
```

UCI 원본 데이터 다운로드:

```bash
python download_data.py
```

성공하면 다음 파일이 생깁니다.

```text
data/abalone.data
data/abalone.names
```

그 뒤 Jupyter를 실행하세요.

```bash
jupyter notebook
```

## 오늘 사용하는 범위
이미 수업에서 다룬 NumPy의 `boolean mask`, `np.where`, `mean/std`, `axis`, `dtype`을 실제 Pandas 데이터에 연결합니다.
새로 익힐 Pandas 핵심은 많지 않습니다.

- `pd.read_csv()`
- `header=None`, `names=...`
- `df.shape`, `df.head()`, `df.dtypes`
- DataFrame Boolean mask
- `to_numpy()`

## 데이터
UCI Machine Learning Repository — Abalone
- 4,177 observations
- 9 columns including target `Rings`
- missing values 없음
- `Rings + 1.5`는 대략적인 나이(years)

테스트 답안 자체는 ZIP에 포함하지 않았습니다. 대신 자동 체크기가 들어 있습니다.

테스트를 다 푼 뒤 **Ctrl+S로 저장하고**, 테스트 노트북 맨 아래 AUTO CHECKER 셀을 실행하세요. 또는 터미널에서:

```bash
python checker.py 03_TEST_TODAY_CHALLENGE.ipynb
```

항목별 통과 여부와 10점 만점 점수를 출력합니다. 8점 이상이면 `TODAY CLEAR!`입니다.
