"""Send the same 3 prompts (2 text, 1 screenshot) at temperature 0, seed 0 to two OpenAI-compatible vLLM servers and
compare the answers (null patch: expect identical; real patch: shows the served model is the edited one).
Usage: python3 osworld/probe_served.py <image.png> [--a http://127.0.0.1:8000/v1 Holo-3.1-4B]
                                       [--b http://127.0.0.1:8001/v1 Holo-3.1-4B-patched]
"""
import base64, json, sys, urllib.request

PROMPTS = ["Describe in two sentences what a computer-use agent should do before declaring a task complete.",
           "List the steps to rename a file in a Linux terminal."]
IMAGE_PROMPT = "What is on this screen? Where would you click to submit?"


def ask(url, model, content):
    body = {"model": model, "messages": [{"role": "user", "content": content}], "temperature": 0, "seed": 0,
            "max_tokens": 64, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(f"{url}/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def main():
    args = sys.argv[1:]
    a = ("http://127.0.0.1:8000/v1", "Holo-3.1-4B"); b = ("http://127.0.0.1:8001/v1", "Holo-3.1-4B-patched")
    if "--a" in args:
        i = args.index("--a"); a = tuple(args[i + 1:i + 3])
    if "--b" in args:
        i = args.index("--b"); b = tuple(args[i + 1:i + 3])
    img = base64.b64encode(open(args[0], "rb").read()).decode()
    contents = [[{"type": "text", "text": p}] for p in PROMPTS]
    contents.append([{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}},
                     {"type": "text", "text": IMAGE_PROMPT}])
    same = []
    for c in contents:
        ra, rb = ask(*a, c), ask(*b, c)
        same.append(ra == rb)
        print(json.dumps({"identical": ra == rb, "a": ra, "b": rb}, ensure_ascii=False))
    print(json.dumps({"all_identical": all(same), "a": a, "b": b}))


if __name__ == "__main__":
    main()
