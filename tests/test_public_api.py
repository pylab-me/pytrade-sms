from __future__ import annotations

import unittest


class PublicFacadeImportTest(unittest.TestCase):
    def test_public_contract_imports(self) -> None:
        import pytrade.sms as sms
        from pytrade.sms.engine import SMSMetadataEngine

        self.assertTrue(hasattr(sms, "SMS"))
        self.assertTrue(hasattr(sms, "query"))
        self.assertTrue(hasattr(sms, "__VERSION__"))
        self.assertIsNotNone(SMSMetadataEngine)


if __name__ == "__main__":
    unittest.main()
