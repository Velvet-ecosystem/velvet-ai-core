# SPDX-License-Identifier: GPL-3.0-only

import ast
import unittest
from pathlib import Path

import velvet


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "velvet"


class Python38BaselineTests(unittest.TestCase):
    def test_public_package_imports(self):
        self.assertIsNotNone(velvet)

    def test_all_core_modules_parse_as_python38(self):
        failures = []
        for path in sorted(PACKAGE.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            try:
                ast.parse(source, filename=str(path), feature_version=8)
            except SyntaxError as exc:
                failures.append(
                    "{}:{}:{}".format(path.relative_to(ROOT), exc.lineno, exc.msg)
                )
        self.assertEqual(
            failures,
            [],
            "Python 3.8 syntax failures: {}".format(failures),
        )


if __name__ == "__main__":
    unittest.main()
