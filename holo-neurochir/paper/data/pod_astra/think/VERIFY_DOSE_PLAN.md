# Independent prospective dose-plan audit

**PASS — numerical calibration/random control, 19 registered jobs (including all 12 dose jobs), 82 rejected mutation cases, exact 6/18 resumption and absolute 20-lot cap.**

RAN: CPU only, sequential hashing/reading of 16 construction captures, independent Euclidean norm computation, fixed PCG64 regeneration, installed validation code with mocked job reads, and a mocked budget ledger. No GPU, generation, active source changes, confirmation task list, or test split/results were accessed. Only this report and the isolated CPU verifier were written.

R31 independently recomputed as **50.02117300961911**: five fixed conclusion tokens per capture, then four samples per task, then four construction tasks equally weighted. It exactly matches the stored calibration; this is a mean of norms, not a norm of averaged vectors. Per-task R31: `{"libreoffice_impress/550ce7e7-747b-495f-b122-acdc4d0b8e54": 49.10943314694856, "libreoffice_impress/08aced46-45a2-48d7-993b-ed3fb5b32302": 50.17867183038404, "multi_apps/716a6079-22da-47f1-ba73-c9d58f986a38": 51.42185412199419, "multi_apps/937087b6-f668-4ba6-9110-60682ee33441": 49.37473293914965}`. Historical difference norm 24.51417350769043 is 0.49007594250091524 × R31.

Random control: all 32×2560 float32 entries match fresh PCG64 seed 271828 bit for bit after unit normalization. Layer-31 norms: learned 0.9999999874669556, random 0.9999999994377732. One immutable random file is shared across all doses. Both arms use layer 31 and the same signed nominal magnitude d×R31 at d=0.5/1/2/4/8/16; amplitude values: `{"0.5": 25.010586504809556, "1": 50.02117300961911, "2": 100.04234601923822, "4": 200.08469203847645, "8": 400.1693840769529, "16": 800.3387681539058}`. Floating-point implementation can introduce tiny rounding differences; matched dose is the declared unit-vector perturbation magnitude.

Prospective requests: all twelve dose files equal their plan and registry entries. Mutated layers, doses, direction paths, skips, seed fields and duplicate indices reject before reservation. Renaming while removing all dose metadata, or borrowing a historical job name with a new dose, now reject via the full registry. Mutation of each of the four new pinned files and duplicate JSON jobs keys in plan/registry reject via frozen-byte hashes. The resume shard hash is checked; altered skip keys or preserved shard bytes reject. **No real lot was reserved; the ledger stayed byte-identical.**

Resumption: exactly the six existing context/sample keys are skipped; seeds are 4000+sample; the other 18 of 24 planned outputs remain. Intervention and contexts match historical lot 5. There are five consumed lots, one exact resume, two dimensionless historical projection jobs, and twelve additions: 5+1+2+12=20. A mocked twentieth lot succeeds and a twenty-first fails. Any extra retry, control or confirmation consumes coverage within that same cap. The old partial arm still requires explicit verified aggregation before a full result.

Stops and exposure: all additions retain protected strata first and early rejection; each job has six finite contexts and four fixed samples. Prospective order stops higher doses after the first protected rejection once the paired random arm is completed, and pauses for control/confirmation after a selective screen. These cross-job decisions are documented/manual, not an unattended controller. The registry references only the four existing construction tasks and five existing screening tasks, matching the prior reserve proof; no new confirmation/test context is introduced or revealed. Fleet preemption remains in force and no launch was performed.

Thread placement: environment thread caps=2 precede numerical imports; torch.set_num_threads(2) immediately follows import torch and precedes model imports.

Limits: **this is a prepared future plan, not a measured dose-response result**. No high-dose behavior, matched-control behavior, confirmation, weight edit or admission is established. The historical two-task fs+ pilot remains exploratory. Verification of the hidden confirmation split relies on the preserved reserve proof and unchanged task sets, without opening that split.

Source/registry hashes: experiment.py `8c33ee5cb907d7fc66fd717757b4399a69e0f174c436555f1954736d85502105`; job_registry.json `a01cbf6323cea0a183f4f066366b941d2ad9f1079a08848f05c50654658815d0`.

Reproduce: `CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 /workspace/venv/bin/python /workspace/astra/astra-think/verify_dose_plan_cpu.py`.
