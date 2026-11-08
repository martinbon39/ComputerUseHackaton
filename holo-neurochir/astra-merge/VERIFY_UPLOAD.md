# Upload wrapper audit

PASS; read-only source audit only. No Modal client, upload, inference, or checkpoint mutation was performed.

`upload.py` validates the checkpoint directory against its local `merge_manifest.json` byte sizes, requires the CLI name to equal the checkpoint directory basename, and invokes exactly:

```text
bash /workspace/modal_put_ckpt.sh <checkpoint> <name> <account>
```

The account is restricted to `1` or `2`. The referenced script preserves the established semantics: account 1 sources `/root/.modal_env`, account 2 sources `/root/.modal_env2`, then `modal volume put --force holo-models <dir> /ckpt/<name>` followed by a destination listing. The wrapper does not alter model files, names, or destination paths.

Modal stdout and stderr are redirected to `DEVNULL` before subprocess return. The wrapper stores only its own safe record: name, numeric account, local checkpoint path, fixed destination, elapsed time, UTC timestamp, subprocess exit code, manifest file metadata/hashes, and the literal `client_output: discarded before storage`. No credential, environment dump, command output, or token identifier is recorded. `check=False` preserves the subprocess return code; `SystemExit(completed.returncode)` propagates it after the record is written.

No actual blocker found. A failed preflight assertion exits before writing a record, which is appropriate because no upload was attempted. Style scan found no new comments, suppressions, TODOs, or workaround markers in `upload.py`.
