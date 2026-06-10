from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SLIME_ROOT = ROOT / "slime"
if str(SLIME_ROOT) not in sys.path:
    sys.path.insert(0, str(SLIME_ROOT))

from drug_agent.gad.data import convert_records
from drug_agent.protocol.react_protocol import parse_react_sequence
from drug_agent.toolrl.convert_react_to_toolrl_steps import convert_react_to_toolrl_steps


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ContractFlowTests(unittest.TestCase):
    def test_kg_task_fixture_keeps_current_contract_markers(self):
        sample = load_fixture("kg_task_v0.2.json")
        self.assertEqual(sample["metadata"]["schema_version"], "kg_task_spec_v0.2")
        self.assertEqual(sample["expected_trajectory"]["schema_version"], "trajectory_v2_graph")
        self.assertIn("tool_order", sample["expected_trajectory"]["execution_plan"])

    def test_trajectory_fixture_keeps_quality_gate_structure(self):
        sample = load_fixture("trajectory_export.json")
        self.assertEqual(sample["status"], "accepted")
        self.assertEqual(sample["reject_reasons"], [])
        self.assertIn("task_metrics", sample)
        self.assertIn("canonical", sample)
        self.assertGreater(sample["molclaw_usage_count"], 0)

    def test_react_fixture_parses_and_derives_toolrl_and_gad_shapes(self):
        sample = load_fixture("react_sft_v1.json")
        for message in sample["messages"]:
            if message["role"] == "assistant":
                parsed = parse_react_sequence(message["content"], role="assistant")
                self.assertTrue(parsed["ok"], parsed)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_path = tmp_path / "react.jsonl"
            output_path = tmp_path / "toolrl.jsonl"
            input_path.write_text(json.dumps(sample) + "\n", encoding="utf-8")
            report = convert_react_to_toolrl_steps(input_path, output_path)
            self.assertEqual(report["kept_rows"], 1)
            toolrl = json.loads(output_path.read_text(encoding="utf-8").strip())

        self.assertEqual(
            set(toolrl),
            {"prompt", "label", "metadata", "target_assistant", "target_tool_calls"},
        )
        self.assertEqual(toolrl["metadata"]["schema_version"], "toolrl_step_v1")
        self.assertEqual(toolrl["metadata"]["target_tool_call_count"], 1)

        gad_rows, skipped, report = convert_records([sample], source="golden")
        self.assertEqual(report["kept"], 2)
        self.assertEqual(skipped, [])
        self.assertEqual(gad_rows[0]["metadata"]["schema_version"], "drug_agent_gad_step_v1")
        self.assertEqual(
            set(gad_rows[0]),
            {"prompt", "state_messages", "teacher_response", "label", "metadata"},
        )


if __name__ == "__main__":
    unittest.main()
