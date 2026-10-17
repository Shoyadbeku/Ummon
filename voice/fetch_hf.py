"""Fetch a HuggingFace model: directly from the Hub if reachable, else from this repo's `hf-models`
GitHub release (filled by .github/workflows/hf-mirror.yml)."""
import argparse
import os
import tarfile
import urllib.request

MIRROR = "https://github.com/Shoyadbeku/Ummon/releases/download/hf-models/{name}.tar.gz"


def fetch(repo: str, dest: str) -> str:
    name = repo.replace("/", "--")
    out = os.path.join(dest, name)
    if os.path.isdir(out):
        return out
    try:
        from huggingface_hub import snapshot_download
        return snapshot_download(repo, local_dir=out)
    except Exception as e:  # Hub blocked -> GitHub release mirror
        print(f"HuggingFace unreachable ({type(e).__name__}); using GitHub mirror")
    os.makedirs(dest, exist_ok=True)
    tgz = out + ".tar.gz"
    urllib.request.urlretrieve(MIRROR.format(name=name), tgz)
    with tarfile.open(tgz) as t:
        t.extractall(dest, filter="data")
    os.remove(tgz)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--dest", default="models")
    a = ap.parse_args()
    print(fetch(a.repo, a.dest))
