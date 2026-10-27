# S48 v2 real-file run (ADVICE ONLY; no Elo claim)

## Fastchess-printed figures (quoted) and exact-GSPRT reproduction

|Gate|Conc|Games|Ptnml(0-2)|Verdict|Elo (printed)|nElo (printed)|LLR (printed)|exact LLR (check)|reproduces|
|---|---:|---:|---|---|---|---|---:|---:|---|
|G100r|5|1500|[5, 121, 458, 154, 12]|cap|10.89 +/- 8.38|22.86 +/- 17.58|2.22|2.2190|yes|
|G104|5|698|[3, 47, 197, 92, 10]|H1|29.44 +/- 13.23|57.67 +/- 25.77|2.95|2.9455|yes|
|G104c|5|1500|[6, 132, 447, 155, 10]|cap|7.18 +/- 8.49|14.87 +/- 17.58|1.23|1.2259|yes|
|G119|5|1500|[9, 130, 435, 163, 13]|cap|9.50 +/- 8.84|18.90 +/- 17.58|1.72|1.7210|yes|
|G120|7|928|[5, 74, 252, 119, 14]|H1|23.62 +/- 11.90|44.52 +/- 22.35|2.99|2.9920|yes|
|G120c|7|1418|[5, 103, 444, 142, 15]|H1|14.46 +/- 8.61|30.43 +/- 18.08|2.98|2.9843|yes|

## Comparability (S48-2 fields)

|Left|Right|Mode|Can compare|Mismatches|Unknown|Notes|
|---|---|---|---|---|---|---|
|G120|G104|rank|False|concurrency|-|-|
|G100r|G119|rank|True|-|-|-|
|G104|G119|rank|True|-|-|-|
|G120|G120c|replicate|True|-|-|-|
|G104|G104c|replicate|True|-|-|-|
|G120c|G104c|rank|False|concurrency|-|-|

## Stopped-Elo selection bias, exact GSPRT model (20000 runs per row; MC interval = simulation error only)

|Gate|Conc|Selection|Assumption|Assumed true Elo|Selected runs|Cond. mean Elo|Bias|Adjusted Elo (model)|Adjusted MC 95%|Observed Elo (printed)|
|---|---:|---|---|---:|---:|---:|---:|---:|---|---|
|G100r|5|cap|observed plug-in|10.89|13819|8.765|-2.125|13.015|[12.965, 13.066]|10.89 +/- 8.38|
|G100r|5|cap|assumed true +10|10.00|15147|8.314|-1.686|12.576|[12.524, 12.627]|10.89 +/- 8.38|
|G104|5|H1|observed plug-in|29.44|19988|30.945|+1.505|27.935|[27.837, 28.033]|29.44 +/- 13.23|
|G104|5|H1|assumed true +10|10.00|3737|18.578|+8.578|20.862|[20.750, 20.973]|29.44 +/- 13.23|
|G119|5|cap|observed plug-in|9.50|16413|8.173|-1.327|10.827|[10.774, 10.881]|9.50 +/- 8.84|
|G119|5|cap|assumed true +10|10.00|15940|8.493|-1.507|11.007|[10.953, 11.061]|9.50 +/- 8.84|
|G120|7|H1|observed plug-in|23.62|19371|25.696|+2.076|21.544|[21.455, 21.633]|23.62 +/- 11.90|
|G120|7|H1|assumed true +10|10.00|3425|19.275|+9.275|14.345|[14.217, 14.473]|23.62 +/- 11.90|

Grids (per-replicate samples) are NOT in git; manifests:

- G100r observed plug-in: `s48v2_G100r_plugin_seed2026102748.jsonl.gz` 99207 bytes sha256 `e65d1915c126bb4fa6a3b5dc674b78ee52a2bbafdfafb861f354b8eb87deb4a3`
- G100r assumed true +10: `s48v2_G100r_true10_seed2026102749.jsonl.gz` 89500 bytes sha256 `1eaa96241df9f50efc2cdd90e850103fd3f8110bb7827e77114b1eb2aac17297`
- G104 observed plug-in: `s48v2_G104_plugin_seed2026102848.jsonl.gz` 155547 bytes sha256 `8c2605b353d85b4b511143c78ab9dfb00486787366dc5a736a9e370a976752af`
- G104 assumed true +10: `s48v2_G104_true10_seed2026102849.jsonl.gz` 82013 bytes sha256 `fccb900690f89176e10b9709b415180678cffda6dfd8c09326df6874268534eb`
- G119 observed plug-in: `s48v2_G119_plugin_seed2026102948.jsonl.gz` 79148 bytes sha256 `855d6a9d02a6a974c66f8ee25636cf35721a090e366db7d0001ecaecef53f261`
- G119 assumed true +10: `s48v2_G119_true10_seed2026102949.jsonl.gz` 83982 bytes sha256 `411a36f3e4c3449bd57d12944e8676673e4448b4fd6fd16cdd022a9686006d53`
- G120 observed plug-in: `s48v2_G120_plugin_seed2026103048.jsonl.gz` 165402 bytes sha256 `d8da50621515b39b07807180ff8589bf9f73033a5e65afaea91596ca2333d981`
- G120 assumed true +10: `s48v2_G120_true10_seed2026103049.jsonl.gz` 79488 bytes sha256 `43ef735d3ca49d14d092b7f1552248f622977975b2e120ed80a9e602f17d801e`
