from django.test import TestCase
from django.contrib.auth.models import User
from .models import Word, UserWordStatus
from .views import get_next_word, update_word_status

class FlashcardTestCase(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create words
        self.words = [
            Word.objects.create(german='vergleichen', translation='to compare'),
            Word.objects.create(german='erklären', translation='to explain'),
            Word.objects.create(german='beeinflussen', translation='to influence'),
            Word.objects.create(german='entwickeln', translation='to develop'),
            Word.objects.create(german='überwinden', translation='to overcome'),
            Word.objects.create(german='ermöglichen', translation='to enable'),
            Word.objects.create(german='verbessern', translation='to improve'),
            Word.objects.create(german='bereitstellen', translation='to provide'),
            Word.objects.create(german='unterstützen', translation='to support'),
            Word.objects.create(german='berücksichtigen', translation='to consider')
        ]

    def test_initial_word_introduction(self):
        # Test that a new word is introduced correctly
        next_word = get_next_word(self.user)
        self.assertIn(next_word, self.words)
        self.assertEqual(UserWordStatus.objects.filter(user=self.user, word=next_word).count(), 1)

    def test_mark_known_learning_to_reviewing_after_two_knowns(self):
        # Transition a word from learning to reviewing after two "known" marks
        word = self.words[0]
        UserWordStatus.objects.create(user=self.user, word=word, status='learning')

        # First known mark should keep it in learning
        update_word_status(self.user, word.id, known=True)
        status = UserWordStatus.objects.get(user=self.user, word=word)
        self.assertEqual(status.status, 'learning')
        self.assertEqual(status.times_known, 1)

        # Second known mark should move it to reviewing
        update_word_status(self.user, word.id, known=True)
        status.refresh_from_db()
        self.assertEqual(status.status, 'reviewing')
        self.assertEqual(status.times_known, 2)

    def test_mark_known_reviewing_to_mastered_after_five_knowns(self):
        # Transition a word from reviewing to mastered after five consecutive knowns
        word = self.words[1]
        UserWordStatus.objects.create(user=self.user, word=word, status='reviewing', known_streak=4)

        # One more known mark should move it to mastered
        update_word_status(self.user, word.id, known=True)
        status = UserWordStatus.objects.get(user=self.user, word=word)
        self.assertEqual(status.status, 'mastered')
        self.assertEqual(status.known_streak, 0)

    def test_mark_unknown_learning_remains_learning(self):
        # Test that marking a learning word as unknown keeps it in learning
        word = self.words[2]
        UserWordStatus.objects.create(user=self.user, word=word, status='learning')
        update_word_status(self.user, word.id, known=False)
        status = UserWordStatus.objects.get(user=self.user, word=word)
        self.assertEqual(status.status, 'learning')
        self.assertEqual(status.known_streak, 0)
        self.assertEqual(status.times_known, 0)

    def test_mark_known_reviewing_increment_streak(self):
        # Test that a reviewing word increments the known streak on each known mark
        word = self.words[3]
        UserWordStatus.objects.create(user=self.user, word=word, status='reviewing', known_streak=2)
        update_word_status(self.user, word.id, known=True)
        status = UserWordStatus.objects.get(user=self.user, word=word)
        self.assertEqual(status.status, 'reviewing')
        self.assertEqual(status.known_streak, 3)

    def test_mark_unknown_reviewing_to_learning(self):
        # Test that marking a reviewing word as unknown moves it back to learning
        word = self.words[4]
        UserWordStatus.objects.create(user=self.user, word=word, status='reviewing', known_streak=3)
        update_word_status(self.user, word.id, known=False)
        status = UserWordStatus.objects.get(user=self.user, word=word)
        self.assertEqual(status.status, 'learning')
        self.assertEqual(status.known_streak, 0)

    def test_introduce_new_words_at_threshold(self):
        # Test that a new word is introduced when the reviewing count is below the threshold
        max_reviewing_words = 10
        num_reviewing = max_reviewing_words - 1  # Set one less than the max limit
        for word in self.words[:num_reviewing]:
            UserWordStatus.objects.create(user=self.user, word=word, status='reviewing')

        next_word = get_next_word(self.user, max_reviewing_words=max_reviewing_words)
        total_user_words = UserWordStatus.objects.filter(user=self.user)
        new_introduced_count = total_user_words.filter(status='learning').count()
        self.assertEqual(new_introduced_count, 1)
        self.assertIsNotNone(next_word)

    def test_no_new_words_introduced_outside_threshold(self):
        # Test that no new words are introduced when the reviewing count meets the threshold
        max_reviewing_words = 10
        for word in self.words[:max_reviewing_words]:
            UserWordStatus.objects.create(user=self.user, word=word, status='reviewing')

        next_word = get_next_word(self.user, max_reviewing_words=max_reviewing_words)
        learning_words = UserWordStatus.objects.filter(user=self.user, status='learning')
        self.assertFalse(learning_words.exists())

    def test_learning_to_reviewing_transition(self):
        # Test the transition from learning to reviewing after two known marks
        word = self.words[5]
        user_word_status = UserWordStatus.objects.create(user=self.user, word=word, status='learning')
        
        update_word_status(self.user, word.id, known=True)
        user_word_status.refresh_from_db()
        self.assertEqual(user_word_status.status, 'learning')

        update_word_status(self.user, word.id, known=True)
        user_word_status.refresh_from_db()
        self.assertEqual(user_word_status.status, 'reviewing')

    def test_consecutive_new_words_limited(self):
        """
        Ensure that get_next_word does not return more than the allowed number of consecutive new words.
        """
        max_new_words_in_a_row = 5  # Set the allowed consecutive new words limit
        reviewing_words_to_create = 3  # Create reviewing words for alternation

        # Set up initial reviewing words to simulate ongoing progress
        for word in self.words[:reviewing_words_to_create]:
            UserWordStatus.objects.create(user=self.user, word=word, status='reviewing')

        new_words_count = 0
        reviewing_words_count = 0
        last_word_id = None

        for _ in range(10):  # Run multiple times to check the alternation behavior
            next_word = get_next_word(self.user, last_word_id=last_word_id, max_consecutive_new_words=max_new_words_in_a_row)
            if next_word:
                user_status = UserWordStatus.objects.get(user=self.user, word=next_word)
                if user_status.status == 'learning':
                    new_words_count += 1
                    reviewing_words_count = 0  # Reset the reviewing count
                elif user_status.status == 'reviewing':
                    reviewing_words_count += 1
                    new_words_count = 0  # Reset the new words count

                # Set last_word_id to avoid immediate repetition
                last_word_id = next_word.id
                
                # Check that we do not exceed consecutive new word limit
                self.assertLessEqual(new_words_count, max_new_words_in_a_row)

                # Optionally check for alternation to ensure reviewing words are returned in between
                if reviewing_words_count > 0:
                    self.assertTrue(new_words_count < max_new_words_in_a_row)

    def test_alternate_with_reviewing_words(self):
        """
        Ensure get_next_word alternates between introducing new words and existing reviewing words.
        """
        # Create a mix of reviewing and new words
        for word in self.words[:5]:
            UserWordStatus.objects.create(user=self.user, word=word, status='reviewing')
        
        reviewing_count = 0
        learning_count = 0
        last_word_id = None

        for _ in range(10):  # Call get_next_word multiple times
            next_word = get_next_word(self.user, last_word_id=last_word_id)
            if next_word:
                user_status = UserWordStatus.objects.get(user=self.user, word=next_word)
                if user_status.status == 'reviewing':
                    reviewing_count += 1
                elif user_status.status == 'learning':
                    learning_count += 1

                # Ensure we alternate and don't have excessive new word introductions
                self.assertTrue(reviewing_count > 0)
                self.assertTrue(learning_count > 0)
                
                # Set last_word_id to avoid repetition
                last_word_id = next_word.id
