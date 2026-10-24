import struct
import unittest

from tg_LogicPulse_bot.services.qr_generator import QrCodeError, generate_qr_png


class QrGenerationTests(unittest.TestCase):
    def test_hd_png_generation(self):
        png = generate_qr_png("https://logicpulse.ru")
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        width, height = struct.unpack(">II", png[16:24])
        self.assertGreaterEqual(width, 800)
        self.assertEqual(width, height)

    def test_empty_content_is_rejected(self):
        with self.assertRaises(QrCodeError):
            generate_qr_png("   ")

    def test_oversized_content_is_rejected(self):
        with self.assertRaises(QrCodeError):
            generate_qr_png("я" * 601)


if __name__ == "__main__":
    unittest.main()
