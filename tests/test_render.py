import asyncio
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from studio.brand import load_brand
from studio.render import output_root, read_design, render


def reject_event_loop_call(function):
    def guarded(*args, **kwargs):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return function(*args, **kwargs)
        raise AssertionError(f"Blocking call on event loop: {function.__qualname__}")

    return guarded


class RenderTests(unittest.IsolatedAsyncioTestCase):
    async def test_local_render_and_read_keep_io_off_event_loop(self):
        report = {"width": 1200, "height": 630}

        def run_renderer(command, **kwargs):
            Path(command[3]).write_bytes(b"png")
            return subprocess.CompletedProcess(command, 0, json.dumps(report).encode())

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            stack.enter_context(patch.dict("os.environ", {"STUDIO_WORKDIR": directory}))
            stack.enter_context(
                patch(
                    "studio.render.subprocess.run",
                    side_effect=reject_event_loop_call(run_renderer),
                )
            )
            for method in (
                "read_text",
                "read_bytes",
                "write_text",
                "write_bytes",
                "mkdir",
                "exists",
            ):
                stack.enter_context(
                    patch.object(
                        Path, method, reject_event_loop_call(getattr(Path, method))
                    )
                )
            stack.enter_context(
                patch("studio.render.output_root", reject_event_loop_call(output_root))
            )
            load_brand.cache_clear()
            self.addCleanup(load_brand.cache_clear)

            result = await render(None, "launch-card", "social-card", "<svg></svg>")
            self.assertEqual(result.png, b"png")
            self.assertEqual(result.report, report)
            self.assertEqual(await read_design(None, "launch-card"), (b"png", report))
            with self.assertRaisesRegex(FileNotFoundError, "Render it first"):
                await read_design(None, "missing-card")

    async def test_cold_tempdir_resolution_runs_off_event_loop(self):
        def run_renderer(command, **kwargs):
            Path(command[3]).write_bytes(b"png")
            return subprocess.CompletedProcess(
                command, 0, b'{"width": 1200, "height": 630}'
            )

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            stack.enter_context(patch.dict("os.environ", {"TMPDIR": directory}))
            stack.enter_context(
                patch("studio.render.os.path.isdir", return_value=False)
            )
            stack.enter_context(patch("tempfile.tempdir", None))
            stack.enter_context(
                patch("studio.render.subprocess.run", side_effect=run_renderer)
            )
            stack.enter_context(patch("os.getcwd", reject_event_loop_call(os.getcwd)))
            stack.enter_context(patch.dict("os.environ"))
            os.environ.pop("STUDIO_WORKDIR", None)

            result = await render(None, "launch-card", "social-card", "<svg></svg>")
            self.assertEqual(
                Path(result.png_path).parent.parent, Path(directory) / "design-studio"
            )
            self.assertEqual((await read_design(None, "launch-card"))[0], b"png")


if __name__ == "__main__":
    unittest.main()
