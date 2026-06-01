import os
import tempfile
import unittest
from unittest.mock import patch

from src import login


class FakeCaptchaResponse:
    content = b"jpeg-bytes"


class FakeSession:
    def __init__(self):
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        return FakeCaptchaResponse()


class FakeSolverResponse:
    def json(self):
        return {"result": "abcd"}


class LoginCaptchaTests(unittest.TestCase):
    def test_get_captcha_writes_to_temp_file_not_cwd(self):
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as cwd:
            image_path = None
            try:
                os.chdir(cwd)
                image_path = login._get_captcha(FakeSession(), "https://example.test/captcha")

                self.assertTrue(os.path.exists(image_path))
                self.assertEqual(os.path.abspath(image_path), image_path)
                self.assertTrue(os.path.basename(image_path).endswith(".jpeg"))
                self.assertFalse(os.path.exists(os.path.join(cwd, "captcha.jpeg")))

                with open(image_path, "rb") as image_file:
                    self.assertEqual(image_file.read(), b"jpeg-bytes")
            finally:
                os.chdir(original_cwd)
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)

    def test_identify_captcha_removes_temp_file_after_upload(self):
        fd, image_path = tempfile.mkstemp(suffix=".jpeg")
        with os.fdopen(fd, "wb") as image_file:
            image_file.write(b"jpeg-bytes")

        with patch.object(login.requests, "post", return_value=FakeSolverResponse()) as post:
            result = login._indentify_captcha(image_path)

        self.assertEqual(result, "abcd")
        self.assertFalse(os.path.exists(image_path))
        post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
