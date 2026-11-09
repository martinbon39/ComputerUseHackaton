"""Frozen OSWorld DIAG/TEST split (written once, before any patch; never change it).
Rule: per domain of test_nogdrive.json, sort task ids by sha1(id); even rank -> DIAG pool, odd -> TEST pool;
keep 120 DIAG + 120 TEST, quota per domain pro rata to domain size (largest remainder), first ids of each pool.
Usage: python make_split.py <test_nogdrive.json> <out_dir>"""
import hashlib, json, math, sys, pathlib
meta = json.load(open(sys.argv[1])); out = pathlib.Path(sys.argv[2]); N = 120
total = sum(len(v) for v in meta.values())
raw = {d: N * len(v) / total for d, v in meta.items()}
quota = {d: math.floor(r) for d, r in raw.items()}
for d in sorted(raw, key=lambda d: (-(raw[d] - quota[d]), d))[: N - sum(quota.values())]:
    quota[d] += 1
diag, test = {}, {}
for d, ids in meta.items():
    s = sorted(ids, key=lambda i: hashlib.sha1(i.encode()).hexdigest())
    diag[d], test[d] = s[0::2][: quota[d]], s[1::2][: quota[d]]
    assert len(diag[d]) == len(test[d]) == quota[d]
assert not set(sum(diag.values(), [])) & set(sum(test.values(), []))
json.dump(diag, open(out / "split_diag.json", "w"), indent=1)
json.dump(test, open(out / "split_test.json", "w"), indent=1)
print("quota", quota, "diag", sum(map(len, diag.values())), "test", sum(map(len, test.values())))
