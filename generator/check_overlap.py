"""Flag questions that are too similar to the reference practice site's questions.

Usage: python generator/check_overlap.py <reference_prompts.json> [threshold]
The reference file is a JSON list of prompt strings (or objects with a "prompt" field). It is not part of
this repository. Similarity is the Jaccard overlap of content words, so it catches reworded copies of the
same task rather than only exact duplicates.
"""
import json
import re
import sys
from pathlib import Path

STOP = set("""a an the of in on at to for from by with and or is are was were be been what which who how many much
does do did show find give list your you it its this that these those than then each per all any as into only
using use first most more least number total""".split())


def words(text):
    return {w for w in re.findall(r"[a-z0-9_]+", text.lower()) if w not in STOP and len(w) > 1}


def main():
    ref = json.loads(Path(sys.argv[1]).read_text())
    ref = [r["prompt"] if isinstance(r, dict) else r for r in ref]
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.45
    content = json.loads((Path(__file__).resolve().parent.parent / "docs" / "data" / "content.json").read_text())
    ours = [(q["id"], q["prompt"]) for q in content["questions"]]
    ours += [(f'{r["id"]}-{q["kind"]}', q["prompt"]) for r in content["regression"] for q in r["questions"]]
    ref_words = [(p, words(p)) for p in ref]
    scored = []
    for qid, prompt in ours:
        w = words(prompt)
        best = max(((len(w & rw) / len(w | rw), p) for p, rw in ref_words if w | rw), default=(0, ""))
        scored.append((best[0], qid, prompt, best[1]))
    scored.sort(reverse=True)
    flagged = [s for s in scored if s[0] >= threshold]
    print(f"{len(ours)} of our questions checked against {len(ref)} reference prompts; "
          f"{len(flagged)} at or above {threshold:.2f} similarity.\n")
    for score, qid, prompt, match in scored[:15]:
        print(f"{score:.2f}  {qid}: {prompt}\n      ref: {match}\n")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
