import importlib.util
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path

spec = importlib.util.spec_from_file_location('capture', Path(__file__).with_name('capture_upstream.py'))
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class CaptureTests(unittest.TestCase):
    def test_empty_oracle_is_not_compatibility(self):
        for output in ('', '\n', '  '):
            with self.assertRaisesRegex(RuntimeError, 'empty'):
                capture.require_prompt(output)

    def test_nonempty_prompt_is_preserved_byte_for_byte(self):
        prompt = '%{\x1b[31m%}main '
        self.assertEqual(capture.require_prompt(prompt), prompt)

    def test_pin_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'oracle'
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError, 'digest mismatch'):
                capture.verify_digest(path, '0' * 64)

    def test_shell_applies_theme_after_source_and_preserves_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / 'zshrc.sh'
            script.write_text('ZSH_THEME_GIT_PROMPT_PREFIX=wrong\n'
                              'git_super_status() { print -rn -- "$ZSH_THEME_GIT_PROMPT_PREFIX"; }\n')
            self.assertEqual(capture.shell_output(root, root, 'raw'), '(')
            script.write_text('git_super_status() { print -u2 failed-oracle; return 7; }\n')
            with self.assertRaisesRegex(RuntimeError, 'failed-oracle'):
                capture.shell_output(root, root, 'raw')

    def test_empty_shell_cannot_overwrite_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'zshrc.sh').write_text('git_super_status() { return 0; }\n')
            fixture = root / 'accepted.json'
            fixture.write_text('accepted')
            argv = ['capture', '--oracle-root', str(root), '--dots-colors', str(root / 'colors'),
                    '--dots-prompt', str(root / 'prompt'), '--output', str(fixture)]
            with patch('sys.argv', argv), patch.object(capture, 'verify_digest'):
                with self.assertRaisesRegex(RuntimeError, 'empty'):
                    capture.main()
            self.assertEqual(fixture.read_text(), 'accepted')


if __name__ == '__main__':
    unittest.main()
