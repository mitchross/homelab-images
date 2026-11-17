"""Bridge NousResearch/hermes-agent#104405 until the constructor setting ships."""

import ast
import hashlib
from pathlib import Path
import sys


OLD = "                agent._memory_manager = _MemoryManager()\n"
NEW = """                # Bound current-turn recall independently of the provider's HTTP timeout.
                import math
                _prefetch_timeout = mem_config.get("external_prefetch_timeout")
                try:
                    if _prefetch_timeout is not None:
                        if isinstance(_prefetch_timeout, bool):
                            raise ValueError("boolean timeout")
                        _prefetch_timeout = float(_prefetch_timeout)
                        if not math.isfinite(_prefetch_timeout) or _prefetch_timeout <= 0:
                            raise ValueError("timeout must be finite and positive")
                except (TypeError, ValueError, OverflowError):
                    logger.warning("Invalid memory.external_prefetch_timeout; using the default")
                    _prefetch_timeout = None
                agent._memory_manager = _MemoryManager(external_prefetch_timeout=_prefetch_timeout)
"""


def apply(root: Path) -> None:
    source = root / "agent/agent_init.py"
    text = source.read_text()
    marker = "# hermes-dev memory-timeout: " + hashlib.sha256(NEW.encode()).hexdigest() + "\n"
    lock = root / "uv.lock"
    lock_text = lock.read_text()
    if text.count(NEW) == 1 and marker in lock_text:
        return
    if text.count(OLD) != 1 or NEW in text:
        raise RuntimeError("Hermes memory init changed; review or remove the timeout bridge")
    patched = text.replace(OLD, NEW)
    ast.parse(patched)
    source.write_text(patched)
    # PM reuses a volume's source snapshot by lock hash; invalidate it without changing dependencies.
    lock.write_text(lock_text + "\n" + marker)


if __name__ == "__main__":
    apply(Path(sys.argv[1]))
