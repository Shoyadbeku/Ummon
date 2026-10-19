# colab.ipynb ni ummon_colab.py dan yig‘adi: python3 colab/build_notebook.py
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'ummon_colab.py'), encoding='utf-8').read()


def code(text, form=True):
    return {'cell_type': 'code', 'metadata': {'cellView': 'form'} if form else {}, 'execution_count': None, 'outputs': [],
            'source': text.splitlines(keepends=True)}


def md(text):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': text.splitlines(keepends=True)}


nb = {
    'nbformat': 4, 'nbformat_minor': 0,
    'metadata': {
        'colab': {'name': 'Ummon Shorts', 'provenance': [], 'gpuType': 'T4'},
        'accelerator': 'GPU',
        'kernelspec': {'name': 'python3', 'display_name': 'Python 3'},
        'language_info': {'name': 'python'},
    },
    'cells': [
        md('# Ummon Shorts · Colab\n'
           'O‘zbekcha AI subtitr: Whisper Colab GPU’sida ishlaydi, subtitrlar videoga kuydiriladi.\n\n'
           '1. **Runtime → Run all** (Ctrl+F9) ni bosing.\n'
           '2. Oxirgi katakda chiqqan `https://….gradio.live` havolasini oching.\n'
           '3. Video yuklang → «Subtitr yaratish» → matnni tuzating → uslub va formatni tanlang → '
           '«Videoni tayyorlash».\n\n'
           'GPU yoqilmagan bo‘lsa: **Runtime → Change runtime type → T4 GPU**.'),
        code('#@title 1. O‘rnatish\n'
             '!pip install -q faster-whisper gradio fonttools\n'
             '!nvidia-smi -L || echo "GPU yo‘q — Runtime → Change runtime type → T4 GPU (CPU da sekin ishlaydi)"\n'),
        md('2. Ilova kodi (o‘zgartirish shart emas)'),
        code('%%writefile ummon_colab.py\n' + src, form=False),
        code('#@title 3. Ishga tushirish — pastda chiqqan gradio.live havolasini oching\n'
             'import importlib, ummon_colab\n'
             'importlib.reload(ummon_colab)\n'
             'ummon_colab.launch(debug=True)\n'),
    ],
}
with open(os.path.join(HERE, '..', 'colab.ipynb'), 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
    f.write('\n')
