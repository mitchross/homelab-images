"""Exercise the installed Hermes init and manager, without a model or memory server."""

import logging
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, "/opt/hermes")
from agent import agent_init
from agent.memory_manager import MemoryManager
from agent.memory_provider import MemoryProvider


class RecallProvider(MemoryProvider):
    name = "regression-recall"

    def is_available(self):
        return True

    def initialize(self, **kwargs):
        pass

    def system_prompt_block(self):
        return ""

    def get_tool_schemas(self):
        return []

    def handle_tool_call(self, name, arguments):
        raise AssertionError("Explicit recall must not be needed")

    def prefetch(self, query, **kwargs):
        threading.Event().wait(0.04)
        return "Radar NG: verify replay PR before resuming"


class MemoryTimeoutTests(unittest.TestCase):
    def initialize(self, value=...):
        config = {"provider": "regression-recall", "memory_enabled": False, "user_profile_enabled": False}
        if value is not ...:
            config["external_prefetch_timeout"] = value
        agent = SimpleNamespace(enabled_toolsets=[], disabled_toolsets=[], _emit_startup_warning=lambda _: None)
        with patch.object(agent_init, "resolve_memory_provider", return_value=RecallProvider()), \
             patch.object(agent_init, "_memory_provider_init_kwargs", return_value={"session_id": "recall-test"}), \
             patch("agent.memory_manager_tools.inject_memory_provider_tools"), \
             patch("agent.safe_worker_policy.safe_worker_enabled", return_value=False):
            agent_init._init_memory(agent, {"memory": config}, False, "desktop")
        self.assertIsNotNone(agent._memory_manager)
        self.addCleanup(agent._memory_manager.shutdown_all)
        return agent._memory_manager

    def test_slow_current_turn_recall_survives_the_configured_bound(self):
        with patch("agent.memory_manager._EXTERNAL_PREFETCH_TIMEOUT_S", 0.01):
            manager = self.initialize(0.2)
            block = manager.prefetch_all("What is unfinished in Radar NG?", session_id="fresh")
        self.assertIn("Radar NG", block)

    def test_unconfigured_bound_still_times_out(self):
        with patch("agent.memory_manager._EXTERNAL_PREFETCH_TIMEOUT_S", 0.01):
            manager = self.initialize()
            self.assertEqual(manager.prefetch_all("Radar NG project history"), "")

    def test_invalid_values_keep_memory_enabled_with_the_default_bound(self):
        for value in (None, "bad", 0, -1, float("inf"), float("nan"), [], True):
            with self.subTest(value=value):
                manager = self.initialize(value)
                self.assertEqual(manager._external_prefetch_timeout, 8.0)

    def test_string_value_and_reused_manager(self):
        manager = self.initialize("125")
        self.assertEqual(manager._external_prefetch_timeout, 125.0)
        agent = SimpleNamespace(enabled_toolsets=[], disabled_toolsets=[])
        with patch("agent.memory_manager_tools.inject_memory_provider_tools"), \
             patch("agent.safe_worker_policy.safe_worker_enabled", return_value=False):
            agent_init._init_memory(agent, {"memory": {}}, False, "desktop", memory_manager=manager)
        self.assertIs(agent._memory_manager, manager)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    with tempfile.TemporaryDirectory() as home, patch.dict("os.environ", {"HERMES_HOME": home, "HOME": home}):
        unittest.main()
