# PROMPT:
# Generate tests for the sample detection pipeline output. Validate that JSONL events
# follow the required schema and include the challenge's re-entry/staff examples.
#
# CHANGES MADE:
# Added checks for REENTRY and staff flags so the sample pipeline demonstrates key edge
# cases even before a trained CV model is uploaded.

import json
from pathlib import Path
from unittest import TestCase

from app.schemas import EventIn
from pipeline.generate_sample_events import generate_sample_events
from tests.helpers import workspace_tempdir


class PipelineEventTests(TestCase):
    def test_sample_pipeline_writes_schema_valid_events(self) -> None:
        with workspace_tempdir() as tmp:
            output = tmp / "events.jsonl"
            count = generate_sample_events(output)
            events = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(count, len(events))
            validated = [EventIn.model_validate(event) for event in events]
            self.assertTrue(any(event.event_type == "REENTRY" for event in validated))
            self.assertTrue(any(event.is_staff for event in validated))
