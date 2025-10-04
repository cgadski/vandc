# vandc

like wandb but without any of the features

## demo

```
$ uv run demo/example.py --d 1000 --beta 0.1
Starting run: have-remain-main-day
Config:
  seed: 42
  d: 1000
  beta: 0.1
  iters: 1000

   Iters      Elapsed Time        Speed       value
 1000/1000  00:00:00<00:00:00  45386.02it/s  8.77+02
100.0% |█████████████████████████████████████████████████████████████████████████████████████|
$ # (run more experiments)
$ uv run python
>>> import vandc
>>> for r in vandc.fetch_all(command_glob="demo/example%", this_commit=True):
...     print(r)
...
<show-new-father-lot (1000 logs): demo/example.py --d 1000 --beta 0.1>
<might-democratic-national-name (1000 logs): demo/example.py --d 1000 --beta 0.2>
<happen-ready-city-law (1000 logs): demo/example.py --d 1000 --beta 0.3>
<fall-poor-party-friend (1000 logs): demo/example.py --d 1000 --beta 0.1>
<have-remain-main-day (1000 logs): demo/example.py --d 1000 --beta 0.1>
>>> vandc.collate_runs(r for r in vandc.fetch_all() if r.config["beta"] <= 0.2)
            value  seed     d  beta  iters
step
0     1005.945312    42  1000   0.1   1000
1     1005.945312    42  1000   0.1   1000
2     1005.945312    42  1000   0.1   1000
3     1005.945312    42  1000   0.1   1000
4     1005.945312    42  1000   0.1   1000
...           ...   ...   ...   ...    ...
995    876.541138    42  1000   0.1   1000
996    876.541138    42  1000   0.1   1000
997    876.541138    42  1000   0.1   1000
998    876.541138    42  1000   0.1   1000
999    876.541138    42  1000   0.1   1000

[4000 rows x 5 columns]
$ uv run demo/graph.py
# (nice seaborn graph built from the collated dataframe)
```

You can also run the `vandc` script to select a single run interactively, and then fetch it using `vandc.fetch("run-name")`.
