"""Split the ONNX model into <15MB parts and fill the page template for publishing."""
import json
import os
import shutil
import sys

onnx_path, vocab_path, ort_dist, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
data = open(onnx_path, "rb").read()
CH = 14 * 1024 * 1024
parts = []
for i in range(0, len(data), CH):
    name = f"model/voice.part{len(parts):02d}.bin"
    os.makedirs(os.path.join(out, "model"), exist_ok=True)
    open(os.path.join(out, name), "wb").write(data[i:i + CH])
    parts.append(name)
for f in ("ort-wasm-simd-threaded.wasm", "ort-wasm-simd-threaded.mjs"):
    shutil.copy(os.path.join(ort_dist, f), out)
here = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(here, "web", "index.html")).read()
html = html.replace("__PARTS__", json.dumps(parts)).replace("__VOCAB__", json.dumps(json.load(open(vocab_path)), ensure_ascii=False))
open(os.path.join(out, "index.html"), "w").write(html)
print(len(parts), "parts")
