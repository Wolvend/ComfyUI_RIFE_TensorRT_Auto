import os
import tempfile
import unittest

import utilities


class FakeResponse:
    def __init__(self, *, content_length, chunks, status_code=200):
        self.headers = {"content-length": str(content_length)}
        self._chunks = chunks
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise ValueError("bad status")

    def iter_content(self, chunk_size=1024):
        for chunk in self._chunks:
            yield chunk


class DownloadFileTests(unittest.TestCase):
    def test_rejects_large_declared_content_length(self):
        def fake_get(*_args, **_kwargs):
            return FakeResponse(content_length=10_000_000_000, chunks=[b"data"])

        original_get = utilities.requests.get
        utilities.requests.get = fake_get
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                target = os.path.join(tmpdir, "file.bin")
                with self.assertRaises(ValueError):
                    utilities.download_file("http://example.com/file", target, max_size_bytes=1024)
        finally:
            utilities.requests.get = original_get

    def test_rejects_when_stream_exceeds_max_size(self):
        def fake_get(*_args, **_kwargs):
            # No content-length header, but streaming exceeds limit
            return FakeResponse(content_length=0, chunks=[b"a" * 1024, b"b" * 1024])

        original_get = utilities.requests.get
        utilities.requests.get = fake_get
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                target = os.path.join(tmpdir, "file.bin")
                with self.assertRaises(ValueError):
                    utilities.download_file("http://example.com/file", target, max_size_bytes=1024)
        finally:
            utilities.requests.get = original_get


if __name__ == "__main__":
    unittest.main()
