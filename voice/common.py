import json
import os
import re

import torch
from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits

from uzbek_text import num_to_uz

LANG = "pt-br"  # closest phonetic spelling to Uzbek Latin among the base model's languages

CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюяўқғҳ",
               ["a", "b", "v", "g", "d", "e", "yo", "j", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r",
                "s", "t", "u", "f", "x", "ts", "ch", "sh", "sh", "'", "i", "", "e", "yu", "ya", "o'", "q",
                "g'", "h"]))

def normalize_uz(text: str) -> str:
    text = text.lower()
    text = "".join(CYR.get(c, c) for c in text)
    text = re.sub(r"[‘’ʻʼ`´]", "'", text)
    text = re.sub(r"\d+", lambda m: " " + num_to_uz(int(m.group())) + " ", text)
    text = re.sub(r"[^a-z' .,!?;:\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_base(model_dir: str, train: bool = False):
    cfg = VitsConfig()
    cfg.load_json(os.path.join(model_dir, "config.json"))
    cfg.model_args.speakers_file = None
    cfg.d_vector_file = None
    cfg.model_args.d_vector_file = None
    cfg.model_args.speaker_encoder_config_path = os.path.join(model_dir, "config_se.json")
    cfg.model_args.speaker_encoder_model_path = os.path.join(model_dir, "model_se.pth")
    cfg.model_args.use_speaker_encoder_as_loss = False
    cfg.model_args.language_ids_file = os.path.join(model_dir, "language_ids.json")
    cfg.language_ids_file = cfg.model_args.language_ids_file
    model = Vits.init_from_config(cfg)
    model.load_checkpoint(cfg, os.path.join(model_dir, "model_file.pth"), eval=not train, strict=False)
    lang_id = json.load(open(cfg.language_ids_file))[LANG]
    return cfg, model, lang_id
