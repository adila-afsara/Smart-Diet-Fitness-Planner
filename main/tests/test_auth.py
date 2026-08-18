from django.test import SimpleTestCase

from main.views import hash_password


class PasswordHashingTests(SimpleTestCase):

    def test_same_password_produces_same_hash(self):
        password = "DietMate123"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        self.assertEqual(
            hash1,
            hash2
        )


    def test_different_passwords_produce_different_hashes(self):
        password1 = "DietMate123"
        password2 = "DietMate456"

        hash1 = hash_password(password1)
        hash2 = hash_password(password2)

        self.assertNotEqual(
            hash1,
            hash2
        )


    def test_password_is_not_stored_as_plain_text(self):
        password = "MySecretPassword"

        hashed_password = hash_password(
            password
        )

        self.assertNotEqual(
            hashed_password,
            password
        )


    def test_sha256_hash_length_is_64(self):
        password = "DietMate123"

        hashed_password = hash_password(
            password
        )

        self.assertEqual(
            len(hashed_password),
            64
        )
