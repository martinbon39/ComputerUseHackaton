"""Text-damage check of an lm_head row edit: a free 200-token English generation at temperature 0 from each server,
with the generated token ids, counting the edited tokens (default a=64, an=276, ans=581, answer=8944) and their
space-prefixed article forms, plus the first divergence from the first server.
Usage: python3 osworld/probe_free_text.py [--server URL=NAME ...] [--ids 64,276,581,8944]
"""
import argparse, json, urllib.request

PROMPT = ("Write a 150-word paragraph explaining how a bicycle works, for a curious child. Use simple words, "
          "mention an example, and finish with an answer to the question: why do we not fall over?")


def generate(url, model):
    body = {"model": model, "messages": [{"role": "user", "content": PROMPT}], "temperature": 0, "seed": 0,
            "max_tokens": 200, "logprobs": True, "top_logprobs": 0, "return_tokens_as_token_ids": True,
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(f"{url}/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        ch = json.load(r)["choices"][0]
    ids = [int(t["token"].split(":")[1]) for t in ch["logprobs"]["content"]]
    return ch["message"]["content"], ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", action="append")
    ap.add_argument("--ids", default="64,276,581,8944")
    a = ap.parse_args()
    servers = [s.split("=", 1) for s in (a.server or ["http://127.0.0.1:8000/v1=Holo-3.1-4B"])]
    watch = [int(i) for i in a.ids.split(",")]
    ref_ids = None
    for url, model in servers:
        text, ids = generate(url, model)
        div = None
        if ref_ids is not None:
            div = next((i for i, (x, y) in enumerate(zip(ref_ids, ids)) if x != y), None if len(ids) == len(ref_ids) else min(len(ids), len(ref_ids)))
        ref_ids = ref_ids or ids
        words = text.lower().split()
        print(json.dumps({"server": f"{url} {model}", "n_tokens": len(ids), "edited_token_counts": {i: ids.count(i) for i in watch},
                          "article_words": {"a": words.count("a"), "an": words.count("an")},
                          "first_divergence_vs_first_server": div, "text": text}, ensure_ascii=False))


if __name__ == "__main__":
    main()
