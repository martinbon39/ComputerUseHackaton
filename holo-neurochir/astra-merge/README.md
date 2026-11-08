# Holo weights-only merge experiment

Owner: astra-merge. Orchestrator: ares. See `REPORT.md` for results and limitations.

The deliverables are complete Hugging Face checkpoints, with the original Holo config, tokenizer, processor, vision tower and explicit output head. Only the language weights change. There are no adapters, gradients or inference modifications.

## Pinned inputs

| Role | Repository | Revision |
|---|---|---|
| Target | Hcompany/Holo-3.1-4B | 8c88265a5a159bfd1492db9243733dd2e6e04a6e |
| Task-vector origin | Qwen/Qwen3.5-4B | 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a |
| Ancestry comparison | Qwen/Qwen3.5-4B-Base | 1001bb4d826a52d1f399e183466143f4da7b741b |
| CUA | OnAnOrange/CUA-Lite-Qwen3.5-4B-ScaleCUA-gpt5_5-epoch3-public | df6eba93efb2df3ed9adc810e0f7f4e038959c74 |
| Fara | microsoft/Fara1.5-4B | 776a33ae5b2ad503796a97ae20fdc66f61d2feea |

The second OnAnOrange repository is a distinct donor and was not used. TMax is excluded because it lacks the vision tower. Source MTP tensors are ignored; all 723 common retained tensors must match shapes exactly. The effective 248,077 token mappings, including decoder-only special tokens, match in both directions across all four models; see `fara_tokenizer_alignment_final.json`.

## Current scope

Ares stopped further Fara and dual/TIES/DARE exploration after the initial seven builds. CUA beta1 failed the full behavior screen. The two remaining construction slots are CUA restricted to layers12–23, beta0.5 then0.25; contrastive RegMean belongs to another agent. Overall cap remains nine constructed checkpoints. See the scope amendment in `REPORT.md`.

## Construction and independent verification

`merge_v1.py` is the frozen builder for the original full-language candidates. `merge_v2.py` adds optional `--layer-range 12 24`, with a half-open interval and explicit manifest field; every unselected tensor is preserved exactly. Arithmetic uses `Holo + beta * mean(donor - Qwen)` in float32, then casts to the original stored dtype. It changes only keys beginning `model.language_model.`. Sparse methods operate on incoming donor deltas, preserving Holo as the anchor:

- TIES retains the largest 20% absolute entries per tensor, elects the summed sign, and averages aligned nonzero entries.
- DARE keeps entries with probability 0.2 and scales survivors by 5, using CPU seed 20261108.

Both sparse variants use donor order CUA then Fara and beta 0.5. This residual TIES construction is not a canonical merge of the Holo and donor task vectors around Qwen.

Pod example, after checking free space and CPU limits:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
taskset -c 40,41 /workspace/venv/bin/python merge_v1.py \
  --donor /dev/shm/astra_merge_cua \
  --output /dev/shm/merge_cua_b050 --beta 0.5 \
  --report cua_b050_build.json
```

An independent session runs `verify_candidate.py CHECKPOINT EVIDENCE_JSON` after each build. It recomputes all language tensors independently, checks all 724 tensors for exact layout/dtype/shape/finiteness, checks 298 preserved tensors bitwise, verifies file hashes and 11 auxiliary files, and loads the local config and processor. CPU builds and these checks are serialized.

`upload.py CHECKPOINT NAME ACCOUNT RECORD_JSON` calls the existing fleet upload script. Client output is discarded before storage because Modal warnings can contain credential identifiers. Upload success does not establish runtime health. Ares and modal-serve own deployments and online evaluation.

## Static screen

On orbit, `screen.py NAME --mode smoke|full --url ENDPOINT` checks model identity before generating. It reads the existing local authentication file without putting its contents into artifacts. The frozen existing probe scripts and six DIAG contexts are identified in `probe_freeze.json` and `cohort.json`. This operational helper retains the absolute orbit paths recorded during the experiment, including `/tmp/astra-merge-work/cohort.json`; archived evidence remains self-contained, but rerunning the helper requires those paths.

Smoke is three generic T=0 prompts and one healthy structured step. Full is three texts plus six contexts with eight seeds each, using T=0.8, top_p=0.9, top_k=20, reflection and the original JSON schema. Do not overwrite a completed output directory. Independent behavioral audits distinguish valid continuation, stopping decisions and actual benchmark success.

No confirmation or test episodes are used to construct or screen candidates. Ares owns the fresh paired 45-task online confirmation and the subsequent 120-task test. Static answer rates over two fs+ and two fs- contexts are not an OSWorld score. Donor training overlap with benchmark tasks remains unknown.

## Storage

The canonical pod experiment is `/workspace/astra/astra-merge/`; `/root/astra_merge_evidence/` is its quota-recovery backup. Complete cloud checkpoints are under account-specific `holo-models:/ckpt/NAME`, loaded as `/models/ckpt/NAME`. The experiment reports identify which accounts contain each candidate. Redundant local checkpoints may be removed only after verified upload, retaining manifests and independent evidence.
