# Runtime verification — astra-tact

Date: 2026-11-08. Lecture indépendante, sans poids chargés par ce lecteur et sans lancement GPU.

## Conclusion

Le premier baseline est un faux négatif d’interception : il a produit des sorties, mais son installation par register_forward_pre_hook sur model.language_model.model n’a jamais observé le forward. Le chemin est structurellement incorrect pour ce modèle Qwen.

model.language_model.model est Qwen3_5Model, déclaré avec @support_torch_compile dans /workspace/vllm-venv/lib/python3.12/site-packages/vllm/model_executor/models/qwen3_5.py:198. Le décorateur fournit son propre __call__ dans .../vllm/compilation/decorators.py:502-507, qui appelle directement self.forward quand la compilation est désactivée. Cela contourne nn.Module._call_impl et donc les forward-pre-hooks du root. Quand la compilation est active, .../decorators.py:576-581 appelle le callable compilé et contourne aussi les hooks enfants.

Le chemin réel V1 appelle self.model(**model_inputs) dans .../vllm/v1/worker/gpu/model_runner.py:1275. apply_model atteint bien ce modèle dans le worker via .../vllm/v1/worker/worker_base.py:128-130; VLLM_ENABLE_V1_MULTIPROCESSING=0 exclut un problème de processus. enforce_eager=True ne désactive que les CUDA graphs (.../vllm/config/vllm.py:1271-1277).

## Correction runtime

Le pilote doit envelopper decoder.forward directement, avec le bound method original capturé avant remplacement :

~~~python
original_forward = decoder.forward

@functools.wraps(original_forward)
def boundary_forward(*args, **kwargs):
    ids = kwargs.get("input_ids", args[0] if args else None)
    embeds = kwargs.get("inputs_embeds", args[3] if len(args) > 3 else None)
    if ids is not None:
        mask = ids == END
    elif embeds is not None:
        mask = (embeds == end_embedding).all(dim=-1)
    else:
        raise RuntimeError("No token IDs or embeddings")
    state["mask"] = mask
    state["boundary_count"] = int(mask.sum().item())
    state["boundary_rows"] += state["boundary_count"]
    state["forward_calls"] += 1
    return original_forward(*args, **kwargs)

decoder.forward = boundary_forward
decoder.do_not_compile = True
~~~

Le wrapper doit être installé avant les layer hooks. Les Qwen3NextDecoderLayer ne portent pas support_torch_compile; leur boucle appelle les layers dans .../vllm/model_executor/models/qwen3_next.py:524-532. Les hooks de layer peuvent donc reconstruire le vrai tuple (hidden_states, residual) et modifier seulement hidden_states. La quantité de bloc utilisée pour la décision est :

~~~python
h = hidden_states.float() + residual.float()
~~~

Le résultat du hook reste (modified_hidden_states, residual), ce qui conserve le résidu séparé vLLM.

Le pilote corrigé doit garder l’assertion de configuration après build_engine() :

~~~python
assert int(llm.llm_engine.vllm_config.compilation_config.mode) == 0
~~~

Le wrapper forward est le point déterministe même lorsque le modèle décoré contourne les hooks. Toute arm doit d’abord observer forward_calls>0 et boundary_rows>0. Le runner exige ensuite target_rows sur les dix couches pour toute intervention. Pour Gate, changed_rows peut légitimement rester à zéro si toutes les projections sont dans la bande : cela prouve seulement un Gate inactif, jamais un gain. Add/random exigent changed_rows>0 et realized_delta_norm_sum>0.

## Gate et Add

Le Gate actuel est bilatéral autour du centroïde :

~~~python
projection = (h - centroid[layer]) @ unit[layer].T
excess = sign(projection) * clamp(abs(projection) - 2*sigma[layer], min=0)
delta = -0.5 * (excess @ unit[layer])
~~~

Il correspond à lambda=0.5 et k=2, agit dans les deux directions et ne modifie rien à l’intérieur de la bande [-2 sigma, 2 sigma].

Pour Add/random, deux échelles doivent rester distinctes :

- échelle littérale : strength * unit.sum(0), avec scaled=False ;
- échelle par norme résiduelle : strength * residual_norm[layer] * unit.sum(0), avec scaled=True.

La seconde est une calibration de magnitude, pas une équivalence au Gate. Les axes appris et aléatoires doivent être comparés après normalisation et orthogonalisation, avec mêmes couches, même force et même convention de signe. Le mock CPU déjà vérifié couvre la projection Gate hors bande et le contrôle random de norme/cosinus ; il ne valide pas le kernel GPU ni le chemin vLLM.

## Génération et schéma conservés

La référence est /workspace/astra/astra-short/generation.py :

- dtype=bfloat16, TP=1, max_model_len=20000, max_num_seqs=4, max_num_batched_tokens=2048 ;
- temperature=0.8, top_p=0.9, top_k=20, max_tokens=3072, seed par requête ;
- sortie contrainte par StructuredOutputsParams(json=Step.model_json_schema()) dans generation.py:208-216 ;
- le parse exige </think>, puis valide strictement le JSON Step dans generation.py:170-205 ;
- END est le token 248069.

Le test de frontière doit compter le token END d’entrée au bloc où son état caché est extrait. Il ne faut pas confondre le token de sortie </think> qui vient d’être échantillonné avec une passe forward qui le prédit.

## Compteurs observés

Le fichier initial baseline_v1.done.json rapporte :

~~~json
{"boundary_rows":0,"forward_calls":0,"changed_rows":0,
 "input_ids_calls":0,"embedding_calls":0}
~~~

Le compteur d’interception de ce baseline est défectueux, mais baseline_v1 reste une référence comportementale valide : le hook de layer retournait la sortie inchangée, donc aucune intervention n’a été appliquée. Ses sorties sont utilisables comme génération originale ; ses compteurs ne prouvent simplement rien sur l’observation du token END.

Les *.done.json ultérieurs montrent que le wrapper d’embeddings fonctionne sur le runtime GPU déjà exécuté :

- gate_v1.done.json : forward_calls=9251, boundary_rows=59, changed_rows=59 ;
- add_m05.done.json : forward_calls=9370, boundary_rows=59, changed_rows=590 ;
- add_m1.done.json : forward_calls=9224, boundary_rows=59, changed_rows=590 ;
- add_m2.done.json : forward_calls=9309, boundary_rows=59, changed_rows=590 ;
- random_m2.done.json : forward_calls=9131, boundary_rows=59, changed_rows=590.

Ces compteurs sont des observations GPU du pilote corrigé, pas un test CPU. Le fait que input_ids_calls=0 et embedding_calls>0 indique que cette voie reçoit des embeddings et utilise la comparaison BF16 exacte avec l’embedding END capturé.

## Contraintes opératoires

Les imports Python sont bornés à deux threads (OMP_NUM_THREADS=2, MKL_NUM_THREADS=2, OPENBLAS_NUM_THREADS=2, torch.set_num_threads(2)). Le pilote garde le STOP /workspace/astra/4b/STOP_GPU, l’échéance/watchdog et le verrou de budget ; toute nouvelle arm doit exiger les compteurs positifs avant d’accepter un résultat.

## Compilation du checkpoint

Un résidu Add compilé dans les poids est une modification constante appliquée à toutes les positions. Elle n’est pas équivalente au Gate END-only et ne doit être étudiée qu’après admission comportementale. La compilation n’a pas été exécutée dans cet audit ; elle est conditionnelle à cette admission et doit vérifier la loadabilité HF complète, la précision BF16 et l’équivalence vLLM sur toutes les positions.
