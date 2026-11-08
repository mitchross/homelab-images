"""CPU-only import and patch-presence checks; inference still requires GPUs."""
import importlib.util
from pathlib import Path
import py_compile

import vllm

root = Path(vllm.__file__).parent
checks = {
    root / "model_executor/layers/quantization/inc/schemes/inc_wna16_linear.py": "method.input_dtype = get_marlin_input_dtype()",
    root / "model_executor/kernels/linear/mixed_precision/marlin.py": "club-3090 W4A8 guards",
    root / "v1/core/single_type_kv_cache_manager.py": "drop_eagle_block and max_num_blocks > 0",
    Path(importlib.util.find_spec("flashinfer").origin).parent / "decode.py": "# [club3090] pin_memory False",
}
for path, marker in checks.items():
    assert marker in path.read_text(), f"Missing patch: {path}"
    py_compile.compile(str(path), doraise=True)
assert "pin_memory=True," not in next(p for p in checks if p.name == "decode.py").read_text()
import os
import shlex
import subprocess
from types import SimpleNamespace

patches = Path('/etc/club3090')
for patch, script in [('effort-budget', 'patch_effort_budget.py'),
                      ('default-thinking-budget', 'patch_default_thinking_budget.py')]:
    subprocess.run(['python3', str(patches / patch / script), 'verify'], check=True)
exports = subprocess.check_output([
    'python3', str(patches / 'effort_budget.py'), 'shell-env', '--engine', 'vllm',
    '--default-effort', 'medium', '--low', '4096', '--medium', '16384', '--xhigh', '32768',
], text=True)
for line in exports.splitlines():
    keyword, assignment = shlex.split(line)
    assert keyword == 'export'
    name, value = assignment.split('=', 1)
    os.environ[name] = value

import club3090_effort_budget_vllm as glue
from vllm import SamplingParams
from transformers.utils.chat_template_utils import _compile_jinja_template

for effort, budget in [('minimal', 4096), ('low', 4096), ('medium', 16384),
                       ('high', 32768), ('max', 32768), ('xhigh', 32768)]:
    request = SimpleNamespace(thinking_token_budget=None, top_k=20)
    glue.apply_effort_budget(request, {'enable_thinking': True, 'reasoning_effort': effort})
    assert request.thinking_token_budget == budget
    request.thinking_token_budget = 123
    glue.apply_effort_budget(request, {'reasoning_effort': effort})
    assert request.thinking_token_budget == 123
assert SamplingParams(top_k=20).thinking_token_budget == 16384
assert SamplingParams(top_k=20, thinking_token_budget=123).thinking_token_budget == 123

template_path = patches / 'qwen38-reasoning-effort-template/chat_template.jinja'
assert (template_path.parent / 'PROVENANCE.md').is_file()
template = _compile_jinja_template(template_path.read_text())
def render(effort):
    return template.render(messages=[{'role': 'user', 'content': 'hello'}],
                           add_generation_prompt=True, enable_thinking=True,
                           reasoning_effort=effort)
assert render('high') == render('xhigh') == render('max')
assert render('minimal') == render('low')
assert render('medium') != render('xhigh')
print(f"vLLM {vllm.__version__}: import, patches, budgets and template checks passed")
