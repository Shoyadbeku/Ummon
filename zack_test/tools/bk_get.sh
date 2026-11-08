#!/bin/bash
# bk_get.sh "<query>" <assetBaseId-prefix> <outdir>  — BlenderKit bepul gltf yuklash
q="$1"; p="$2"; out="$3"; mkdir -p "$out"
meta=$(curl -sS -G "https://www.blenderkit.com/api/v1/search/" --data-urlencode "query=$q asset_type:model is_free:true" --data-urlencode "page_size=20")
dl=$(echo "$meta" | python3 -c "
import json,sys; p='$p'
d=next(x for x in json.load(sys.stdin)['results'] if x['assetBaseId'].startswith(p))
print([f['downloadUrl'] for f in d['files'] if f['fileType']=='gltf'][0]); print(d['name'], '|', d.get('license'), file=sys.stderr)")
fp=$(curl -sS "$dl?scene_uuid=$(python3 -c 'import uuid;print(uuid.uuid4())')" | python3 -c "import json,sys; print(json.load(sys.stdin)['filePath'])")
curl -sS -o "$out/$p.glb" "$fp" && ls -la "$out/$p.glb" | awk '{print $5/1048576 " MB", $9}'
