# PROMPT:
# Switch the production detection path to YOLOE-26 and add anonymous staff/customer
# role identity metadata without relying on face recognition.
#
# CHANGES MADE:
# Added tests that protect the YOLOE-26 default model and the role-classification
# contract used by the dashboard and event metadata.

from pathlib import Path
from unittest import TestCase

from pipeline.detect import DEFAULT_DETECTOR_MODEL, VideoProcessor
from pipeline.staff import classify_person_role


class YoloeDefaultTests(TestCase):
    def test_missing_custom_model_falls_back_to_yoloe_26(self) -> None:
        source = VideoProcessor._resolve_model_source(Path("models/does-not-exist.pt"))

        self.assertEqual(source, DEFAULT_DETECTOR_MODEL)
        self.assertEqual(source, "yoloe-26s-seg.pt")

    def test_role_classifier_returns_anonymous_customer_without_face_identity(self) -> None:
        role = classify_person_role(None, (0, 0, 10, 10), camera_id="CAM_1")

        self.assertEqual(role.label, "customer")
        self.assertFalse(role.is_staff)
        self.assertGreater(role.confidence, 0)
        self.assertNotIn("face_id", role.signals)
