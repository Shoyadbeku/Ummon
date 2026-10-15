"""Minimal LoRA for Conv1d / Linear layers (supports dilation & padding, unlike generic libs)."""
import torch
import torch.nn as nn


class LoRAConv1d(nn.Module):
    def __init__(self, base: nn.Conv1d, r: int, alpha: float):
        super().__init__()
        self.base = base
        self.scale = alpha / r
        self.lora_A = nn.Conv1d(base.in_channels, r, base.kernel_size[0], stride=base.stride[0],
                                padding=base.padding[0], dilation=base.dilation[0], bias=False)
        self.lora_B = nn.Conv1d(r, base.out_channels, 1, bias=False)
        nn.init.kaiming_uniform_(self.lora_A.weight, a=5 ** 0.5)
        nn.init.zeros_(self.lora_B.weight)

    def forward(self, x):
        return self.base(x) + self.lora_B(self.lora_A(x)) * self.scale


class LoRALinear(nn.Module):
    def __init__(self, base: nn.Linear, r: int, alpha: float):
        super().__init__()
        self.base = base
        self.scale = alpha / r
        self.lora_A = nn.Linear(base.in_features, r, bias=False)
        self.lora_B = nn.Linear(r, base.out_features, bias=False)
        nn.init.kaiming_uniform_(self.lora_A.weight, a=5 ** 0.5)
        nn.init.zeros_(self.lora_B.weight)

    def forward(self, x):
        return self.base(x) + self.lora_B(self.lora_A(x)) * self.scale


TARGETS = ("text_encoder", "duration_predictor", "flow", "waveform_decoder")


def inject_lora(model: nn.Module, r: int = 16, alpha: float = 16, targets=TARGETS) -> int:
    """Wrap every grouped=1 Conv1d/Linear under `targets` with a LoRA adapter. Returns count."""
    n = 0
    for t in targets:
        root = getattr(model, t)
        for parent_name, parent in list(root.named_modules()):
            for name, child in list(parent._modules.items()):
                if isinstance(child, (LoRAConv1d, LoRALinear)) or child is None:
                    continue
                if isinstance(child, nn.Conv1d) and child.groups == 1:
                    parent._modules[name] = LoRAConv1d(child, r, alpha)
                    n += 1
                elif isinstance(child, nn.Linear):
                    parent._modules[name] = LoRALinear(child, r, alpha)
                    n += 1
    return n


def lora_state_dict(model: nn.Module, extra=("emb_l.",)) -> dict:
    return {k: v.detach().cpu() for k, v in model.state_dict().items()
            if "lora_" in k or any(k.startswith(e) for e in extra)}
