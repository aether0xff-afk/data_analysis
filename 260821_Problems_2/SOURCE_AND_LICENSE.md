# Source and dataset note

Base dataset: **UCI Machine Learning Repository — Air Quality**

- Dataset: Air Quality
- Creator: Saverio De Vito
- DOI: https://doi.org/10.24432/C59K5F
- UCI page: https://archive.ics.uci.edu/dataset/360/air+quality

UCI describes 9,358 hourly records and states that missing values are tagged with `-200`.

## Important

The challenge files named `AirQuality_DIRTY_*.csv` are **not untouched UCI originals**.
`setup_data.py` downloads a mirror of the UCI data and deterministically adds educational corruption:

- extra whitespace in headers / date-time strings
- `?`, `NA`, `error` tokens inside numeric columns
- invalid date strings
- duplicate rows
- shuffled row order
- one entirely empty junk column

This is done only to create a reproducible data-cleaning exercise.
The script uses fixed random seeds so the checker can grade the result.
