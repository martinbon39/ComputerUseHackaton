from common import *
import argparse
import signal
import time


def snapshot():
    result = {}
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
            result[int(path.name)] = dict(parent=int(fields[1]), start=fields[19], state=fields[0])
        except (OSError, IndexError):
            continue
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    args = ap.parse_args()
    roots = [args.pid]
    marker = ROOT / "server.pid"
    if marker.exists():
        roots.append(int(marker.read_text()))
    states = snapshot()
    for pid in roots:
        if pid not in states:
            continue
        command = (Path("/proc") / str(pid) / "cmdline").read_bytes().replace(b"\0", b" ").decode()
        assert "/dev/shm/astra-regmean/serve_fp16.sh" in command or (any(x in command for x in ["--served-model-name regmean_original_fp16", "--served-model-name regmean_cua_centered_fp16"]) and "--port 8023" in command), command
    owned = {pid for pid in roots if pid in states}
    for _ in range(len(states)):
        more = {pid for pid, s in states.items() if s["parent"] in owned} - owned
        if not more:
            break
        owned.update(more)
    identities = {pid: states[pid]["start"] for pid in owned}
    for sig in [signal.SIGTERM, signal.SIGKILL]:
        current = snapshot()
        for pid, start in identities.items():
            if pid in current and current[pid]["start"] == start and current[pid]["state"] != "Z":
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    continue
        for _ in range(20):
            current = snapshot()
            live = [pid for pid, start in identities.items() if pid in current and current[pid]["start"] == start and current[pid]["state"] != "Z"]
            if not live:
                break
            time.sleep(.5)
        if not live:
            break
    assert not live, live
    write_json(ROOT / "server_cleanup_fp16.json", dict(root=args.pid, identities=identities, all_exited=True))
    marker.unlink(missing_ok=True)
    print(json.dumps(dict(root=args.pid, owned=len(identities), all_exited=True)))


if __name__ == "__main__":
    main()
