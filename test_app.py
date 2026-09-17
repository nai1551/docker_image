import unittest
from unittest.mock import patch, MagicMock
import app as flask_app


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        self.client = flask_app.app.test_client()
        self.client.testing = True

    @patch("app.get_connection")
    def test_home_page_loads(self, mock_get_connection):
        # Mock the DB so no real MySQL connection is needed during tests
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add a note", response.data)

    @patch("app.get_connection")
    def test_post_note_inserts_and_redisplays(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, "Test note from pytest")]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        response = self.client.post("/", data={"message": "Test note from pytest"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test note from pytest", response.data)
        mock_cursor.execute.assert_any_call(
            "INSERT INTO notes (message) VALUES (%s)", ("Test note from pytest",)
        )

    @patch("app.get_connection")
    def test_empty_message_not_inserted(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        self.client.post("/", data={"message": ""})
        insert_calls = [
            c for c in mock_cursor.execute.call_args_list
            if "INSERT INTO notes" in str(c)
        ]
        self.assertEqual(len(insert_calls), 0)


if __name__ == "__main__":
    unittest.main()
