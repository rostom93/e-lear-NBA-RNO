from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class ChatbotAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_keyword_reply(self):
        response = self.client.post(
            "/api/chatbot/",
            {"message": "Comment acheter des crédits ?"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("crédits", response.data["reply"].lower())

    def test_default_reply(self):
        response = self.client.post(
            "/api/chatbot/",
            {"message": "zzzz unknown"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("mots-clés", response.data["reply"].lower())
