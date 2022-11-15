from unittest import TestCase
import testutils


class Test(TestCase):
    @classmethod
    def setup_class(cls):
        print("\r\nCreating lambda")
        testutils.create_lambda("lambda")

    @classmethod
    def teardown_class(cls):
        print("\r\nTearing down lambda")
        testutils.delete_lambda("lambda")

    def test_lambda_returns_correct(self):
        payload = testutils.invoke_function("lambda")
        print(payload)
        self.assertEqual(payload["response"], "success")
