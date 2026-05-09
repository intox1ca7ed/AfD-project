# Historical Manual Polling Sanity Check Report

- Validation timestamp: 2026-05-08T23:45:36
- Poll-level CSV: `C:\PythonProjects\AfD-project\data\polling\manual\afd_polling_historical_manual_polllevel.csv`
- Monthly CSV: `C:\PythonProjects\AfD-project\data\polling\manual\afd_polling_historical_manual_monthly.csv`
- Monthly parquet: `C:\PythonProjects\AfD-project\data\polling\manual\afd_polling_historical_manual_monthly.parquet`

## Row Counts
- Poll-level rows: 175
- Monthly rows: 40

## Coverage
- Poll-level date range: 2013-09-22 to 2016-12-16
- Monthly coverage range: 2013-09 to 2016-12
- Missing months in full expected range (2013-09..2016-12): none
- Cologne target window 2015-07..2016-06 fully covered: yes

## Pollsters
- Infratest dimap: 79
- Politbarometer: 60
- GMS: 36
- Unexpected pollster labels: none

## Value Ranges
- Poll-level afd_pct: min=3.000, max=16.000, mean=7.518, median=6.000
- Monthly afd_poll_support_mean: min=3.333, max=14.333, mean=7.609, median=6.100
- Plausible range [0,30] check: pass

## Duplicate Check
- Exact duplicate count (poll_date + pollster + afd_pct + source_url): 0

## Aggregation Consistency
- Result: passed

## Monthly Snapshot

First 10 monthly rows:

| month   | year_month   | month_dt   |   year |   month_num |   afd_poll_support_mean |   afd_poll_support_median |   afd_poll_support_min |   afd_poll_support_max |   afd_poll_support_sd |   n_polls |   n_pollsters | first_poll_date   | last_poll_date   | source       | collection_method                      | notes                                                                       |
|:--------|:-------------|:-----------|-------:|------------:|------------------------:|--------------------------:|-----------------------:|-----------------------:|----------------------:|----------:|--------------:|:------------------|:-----------------|:-------------|:---------------------------------------|:----------------------------------------------------------------------------|
| 2013-09 | 2013-09      | 2013-09-01 |   2013 |           9 |                   4.775 |                       4.7 |                    4.7 |                      5 |              0.15     |         4 |             3 | 2013-09-22        | 2013-09-27       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2013-10 | 2013-10      | 2013-10-01 |   2013 |          10 |                   5.125 |                       5   |                    4.5 |                      6 |              0.629153 |         4 |             3 | 2013-10-10        | 2013-10-25       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2013-11 | 2013-11      | 2013-11-01 |   2013 |          11 |                   4.6   |                       5   |                    4   |                      5 |              0.547723 |         5 |             3 | 2013-11-07        | 2013-11-29       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2013-12 | 2013-12      | 2013-12-01 |   2013 |          12 |                   4     |                       4   |                    4   |                      4 |              0        |         4 |             3 | 2013-12-05        | 2013-12-20       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2014-01 | 2014-01      | 2014-01-01 |   2014 |           1 |                   4     |                       4   |                    4   |                      4 |              0        |         5 |             3 | 2014-01-09        | 2014-01-31       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2014-02 | 2014-02      | 2014-02-01 |   2014 |           2 |                   4.75  |                       5   |                    4   |                      5 |              0.5      |         4 |             3 | 2014-02-06        | 2014-02-28       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2014-03 | 2014-03      | 2014-03-01 |   2014 |           3 |                   4.6   |                       5   |                    4   |                      5 |              0.547723 |         5 |             3 | 2014-03-06        | 2014-03-28       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2014-04 | 2014-04      | 2014-04-01 |   2014 |           4 |                   5     |                       5   |                    4   |                      6 |              0.707107 |         5 |             3 | 2014-04-03        | 2014-04-30       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2014-05 | 2014-05      | 2014-05-01 |   2014 |           5 |                   5     |                       5   |                    4   |                      6 |              1        |         3 |             3 | 2014-05-09        | 2014-05-16       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2014-06 | 2014-06      | 2014-06-01 |   2014 |           6 |                   6     |                       6   |                    5   |                      7 |              0.707107 |         5 |             3 | 2014-06-05        | 2014-06-27       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |

Last 10 monthly rows:

| month   | year_month   | month_dt   |   year |   month_num |   afd_poll_support_mean |   afd_poll_support_median |   afd_poll_support_min |   afd_poll_support_max |   afd_poll_support_sd |   n_polls |   n_pollsters | first_poll_date   | last_poll_date   | source       | collection_method                      | notes                                                                       |
|:--------|:-------------|:-----------|-------:|------------:|------------------------:|--------------------------:|-----------------------:|-----------------------:|----------------------:|----------:|--------------:|:------------------|:-----------------|:-------------|:---------------------------------------|:----------------------------------------------------------------------------|
| 2016-03 | 2016-03      | 2016-03-01 |   2016 |           3 |                 13      |                      13   |                     12 |                     14 |              1        |         3 |             3 | 2016-03-17        | 2016-03-24       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-04 | 2016-04      | 2016-04-01 |   2016 |           4 |                 12.6    |                      12   |                     11 |                     14 |              1.34164  |         5 |             3 | 2016-04-07        | 2016-04-22       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-05 | 2016-05      | 2016-05-01 |   2016 |           5 |                 14.3333 |                      15   |                     13 |                     15 |              1.1547   |         3 |             2 | 2016-05-04        | 2016-05-20       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-06 | 2016-06      | 2016-06-01 |   2016 |           6 |                 13.4    |                      13   |                     12 |                     15 |              1.14018  |         5 |             3 | 2016-06-02        | 2016-06-24       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-07 | 2016-07      | 2016-07-01 |   2016 |           7 |                 11      |                      11   |                      9 |                     12 |              1.22474  |         5 |             3 | 2016-07-07        | 2016-07-22       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-08 | 2016-08      | 2016-08-01 |   2016 |           8 |                 12      |                      12   |                     11 |                     13 |              1        |         3 |             2 | 2016-08-04        | 2016-08-26       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-09 | 2016-09      | 2016-09-01 |   2016 |           9 |                 14      |                      13.5 |                     13 |                     16 |              1.41421  |         4 |             3 | 2016-09-01        | 2016-09-23       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-10 | 2016-10      | 2016-10-01 |   2016 |          10 |                 13.2    |                      13   |                     12 |                     14 |              0.83666  |         5 |             3 | 2016-10-06        | 2016-10-28       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-11 | 2016-11      | 2016-11-01 |   2016 |          11 |                 12.4    |                      12   |                     12 |                     13 |              0.547723 |         5 |             3 | 2016-11-03        | 2016-11-25       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-12 | 2016-12      | 2016-12-01 |   2016 |          12 |                 12.6667 |                      13   |                     12 |                     13 |              0.57735  |         3 |             2 | 2016-12-08        | 2016-12-16       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |

Cologne-window monthly rows (2015-07..2016-06):

| month   | year_month   | month_dt   |   year |   month_num |   afd_poll_support_mean |   afd_poll_support_median |   afd_poll_support_min |   afd_poll_support_max |   afd_poll_support_sd |   n_polls |   n_pollsters | first_poll_date   | last_poll_date   | source       | collection_method                      | notes                                                                       |
|:--------|:-------------|:-----------|-------:|------------:|------------------------:|--------------------------:|-----------------------:|-----------------------:|----------------------:|----------:|--------------:|:------------------|:-----------------|:-------------|:---------------------------------------|:----------------------------------------------------------------------------|
| 2015-07 | 2015-07      | 2015-07-01 |   2015 |           7 |                 4.16667 |                         4 |                      4 |                      5 |              0.408248 |         6 |             3 | 2015-07-02        | 2015-07-30       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2015-08 | 2015-08      | 2015-08-01 |   2015 |           8 |                 3.33333 |                         3 |                      3 |                      4 |              0.57735  |         3 |             3 | 2015-08-14        | 2015-08-27       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2015-09 | 2015-09      | 2015-09-01 |   2015 |           9 |                 4.2     |                         4 |                      4 |                      5 |              0.447214 |         5 |             3 | 2015-09-03        | 2015-09-25       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2015-10 | 2015-10      | 2015-10-01 |   2015 |          10 |                 6.2     |                         6 |                      5 |                      8 |              1.09545  |         5 |             3 | 2015-10-01        | 2015-10-23       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2015-11 | 2015-11      | 2015-11-01 |   2015 |          11 |                 8.6     |                         9 |                      8 |                      9 |              0.547723 |         5 |             3 | 2015-11-05        | 2015-11-27       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2015-12 | 2015-12      | 2015-12-01 |   2015 |          12 |                 9.66667 |                        10 |                      9 |                     10 |              0.57735  |         3 |             2 | 2015-12-03        | 2015-12-18       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-01 | 2016-01      | 2016-01-01 |   2016 |           1 |                10       |                        10 |                      9 |                     11 |              1        |         5 |             3 | 2016-01-04        | 2016-01-29       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-02 | 2016-02      | 2016-02-01 |   2016 |           2 |                10.8     |                        11 |                     10 |                     12 |              0.83666  |         5 |             3 | 2016-02-03        | 2016-02-29       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-03 | 2016-03      | 2016-03-01 |   2016 |           3 |                13       |                        13 |                     12 |                     14 |              1        |         3 |             3 | 2016-03-17        | 2016-03-24       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-04 | 2016-04      | 2016-04-01 |   2016 |           4 |                12.6     |                        12 |                     11 |                     14 |              1.34164  |         5 |             3 | 2016-04-07        | 2016-04-22       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-05 | 2016-05      | 2016-05-01 |   2016 |           5 |                14.3333  |                        15 |                     13 |                     15 |              1.1547   |         3 |             2 | 2016-05-04        | 2016-05-20       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |
| 2016-06 | 2016-06      | 2016-06-01 |   2016 |           6 |                13.4     |                        13 |                     12 |                     15 |              1.14018  |         5 |             3 | 2016-06-02        | 2016-06-24       | Wahlrecht.de | manual_wahlrecht_historical_supplement | Pre-DAWUM historical supplement for Cologne-period descriptive diagnostics. |

## Output Artifacts
- Figure: `C:\PythonProjects\AfD-project\figures\05a_historical_polling_sanity_check\afd_polling_historical_manual_monthly.png`

## Warnings
- none

## Errors
- none

## Final Status
- PASS