"""Cap each OSWorld docker VM container's memory (shared prod VPS) and optionally mount a network.sh
using iptables-nft, and bind VM ports to 127.0.0.1 only (host has no legacy nat table; OSW_NETWORK_SH=<path>). Idempotent.
Usage: python patch_provider_mem.py <OSWorld>/desktop_env/providers/docker/provider.py"""
import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
old = '''                    cap_add=["NET_ADMIN"],'''
new = '''                    cap_add=["NET_ADMIN"],
                    mem_limit=os.environ.get("OSW_MEM_LIMIT", "5g"),
                    memswap_limit=os.environ.get("OSW_MEM_LIMIT", "5g"),'''
old2 = '''                        os.path.abspath(path_to_vm): {
                            "bind": "/System.qcow2",
                            "mode": "ro"
                        }'''
new2 = old2 + ''',
                        **({os.environ["OSW_NETWORK_SH"]: {"bind": "/run/network.sh", "mode": "ro"}}
                           if os.environ.get("OSW_NETWORK_SH") else {})'''
if new not in s:
    assert old in s, "provider.py changed: patch target not found"
    s = s.replace(old, new)
if new2 not in s:
    assert old2 in s, "provider.py changed: volume patch target not found"
    s = s.replace(old2, new2)
old3 = '''                        8006: self.vnc_port,
                        5000: self.server_port,
                        9222: self.chromium_port,
                        8080: self.vlc_port'''
new3 = '''                        8006: ("127.0.0.1", self.vnc_port),
                        5000: ("127.0.0.1", self.server_port),
                        9222: ("127.0.0.1", self.chromium_port),
                        8080: ("127.0.0.1", self.vlc_port)'''
if new3 not in s:
    assert old3 in s, "provider.py changed: ports patch target not found"
    s = s.replace(old3, new3)
p.write_text(s)
print("patched", p)
