import unittest

from telemetry.config import SystemConfig
from telemetry.models import BOOLEAN, SCALAR, TelemetryValue
from telemetry.validator import ValueValidator


def tv(kind, value):
    return TelemetryValue("SRC_1", "OBJ_1", kind, value, 0.0)


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.v = ValueValidator(SystemConfig())

    def test_valid_scalar(self):
        self.assertIsNone(self.v.validate(tv(SCALAR, 42.5)))
        self.assertIsNone(self.v.validate(tv(SCALAR, -1000)))

    def test_valid_bool(self):
        self.assertIsNone(self.v.validate(tv(BOOLEAN, True)))
        self.assertIsNone(self.v.validate(tv(BOOLEAN, False)))

    def test_wrong_type(self):
        self.assertIsNotNone(self.v.validate(tv(SCALAR, "abc")))
        self.assertIsNotNone(self.v.validate(tv(BOOLEAN, 1)))

    def test_nan_inf(self):
        self.assertIsNotNone(self.v.validate(tv(SCALAR, float("nan"))))
        self.assertIsNotNone(self.v.validate(tv(SCALAR, float("inf"))))

    def test_out_of_range(self):
        self.assertIsNotNone(self.v.validate(tv(SCALAR, 10**9)))

    def test_unknown_kind(self):
        self.assertIsNotNone(self.v.validate(tv("weird", 1)))


if __name__ == "__main__":
    unittest.main()
