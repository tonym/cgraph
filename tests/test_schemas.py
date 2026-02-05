import json
import unittest
from pathlib import Path

from cgraph.observe import OBSERVATION_SCHEMA_VERSION


class SchemaTests(unittest.TestCase):
    def test_schema_files_are_valid_json(self) -> None:
        schema_dir = Path(__file__).resolve().parents[1] / "cgraph" / "schemas"
        schemas = sorted(schema_dir.glob("*.json"))
        self.assertTrue(schemas, "No schema files found")
        for path in schemas:
            with self.subTest(path=path.name):
                data = json.loads(path.read_text())
                self.assertIn("$schema", data)
                self.assertIn("$id", data)

    def test_observation_schema_version_matches(self) -> None:
        schema_dir = Path(__file__).resolve().parents[1] / "cgraph" / "schemas"
        observation_schema = json.loads((schema_dir / "observation-index.schema.json").read_text())
        version = observation_schema["properties"]["schema_version"]["const"]
        self.assertEqual(version, OBSERVATION_SCHEMA_VERSION)
