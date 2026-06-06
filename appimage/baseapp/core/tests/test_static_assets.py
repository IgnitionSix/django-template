from pathlib import Path

from django.test import SimpleTestCase


REPO_ROOT = Path(__file__).resolve().parents[4]


class StaticAssetConfigTests(SimpleTestCase):
    def test_tailwind_content_globs_do_not_scan_python_tests(self):
        tailwind_config = (
            REPO_ROOT
            / "appimage"
            / "baseapp"
            / "core"
            / "static_src"
            / "tailwind.config.js"
        ).read_text()

        self.assertNotIn("../../core/**/*.py", tailwind_config)
        self.assertIn("../../core/templates/**/*.html", tailwind_config)
