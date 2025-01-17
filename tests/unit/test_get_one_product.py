import unittest
import json
import pymysql
from botocore.exceptions import ClientError

from get_one_product import app
from unittest.mock import patch

mock_product = {
    "id": 1,
    "name": "Test product",
    "price": 10.0,
    "status": 1,
    "category_id": 1,
    "category_name": "Test category",
    "image": "test.jpg"
}

mock_success ={
    "pathParameters": {
        "id": "1"
    }
}

mock_missing_fields = {}

mock_invalid_type ={
    "pathParameters": {
        "id": "aasdasd"
    }
}

mock_invalid_id ={
    "pathParameters": {
        "id": "0"
    }
}

mock_not_found_id = {
    "pathParameters": {
        "id": "999"
    }
}

class TestGetOneProduct(unittest.TestCase):
    @patch("get_one_product.app.get_product")
    def test_get_one_product_success(self, mock_get_product):
        mock_get_product.return_value = mock_product
        result = app.lambda_handler(mock_success, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertIn("product", body)

    def test_get_one_product_missing_fields(self):
        result = app.lambda_handler(mock_missing_fields, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "MISSING_PRODUCT_ID")

    def test_get_one_product_invalid_field_type(self):
        result = app.lambda_handler(mock_invalid_type, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INVALID_PRODUCT_ID")

    def test_get_one_product_invalid_id(self):
        result = app.lambda_handler(mock_invalid_id, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INVALID_PRODUCT_ID")

    def test_product_not_found(self):
        result = app.lambda_handler(mock_not_found_id, None)
        self.assertEqual(result["statusCode"], 404)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "PRODUCT_NOT_FOUND")

    @patch('get_one_product.app.get_product')
    def test_internal_server_error(self, mock_get_product):
        mock_get_product.side_effect = Exception("ERROR CHECKING IF PRODUCT EXISTS")

        result = app.lambda_handler(mock_success, None)
        self.assertEqual(result["statusCode"], 404)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "PRODUCT_NOT_FOUND")
        self.assertIn("ERROR CHECKING IF PRODUCT EXISTS", body["error"])

    @patch('get_one_product.app.pymysql.connect')
    def test_connect_to_database_mysql_exception(self, mock_connect):
        mock_connect.side_effect = pymysql.MySQLError("MySQL connection error")

        with self.assertRaises(Exception) as context:
            app.connect_to_database()

        self.assertIn("ERROR CONNECTING TO DATABASE", str(context.exception))
        self.assertIn("MySQL connection error", str(context.exception))

    @patch('get_one_product.app.int')
    def test_lambda_handler_internal_server_error(self, mock_int):
        mock_int.side_effect = Exception("Simulated internal error")

        result = app.lambda_handler(mock_success, None)

        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")
        self.assertIn("Simulated internal error", body["error"])

    @patch("get_one_product.app.boto3.session.Session.client")
    def test_get_secret_client_error(self, mock_client):
        # Simula la excepción ClientError
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            operation_name='GetSecretValue'
        )

        with self.assertRaises(ClientError):
            app.get_secret()
    def test_decimal_to_float_invalid_type(self):
        with self.assertRaises(TypeError):
            app.decimal_to_float("string")