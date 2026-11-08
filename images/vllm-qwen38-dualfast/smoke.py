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
print(f"vLLM {vllm.__version__}: import and all four patch checks passed")
