# flashcards/management/commands/import_german_words.py

import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from flashcards.models import Word, Stack

class Command(BaseCommand):
    help = 'Import German words into the database, organized into stacks. Each JSON file in the data directory represents one stack.'

    def handle(self, *args, **options):
        data_directory = os.path.join(settings.BASE_DIR, 'flashcards', 'data')
        
        if not os.path.exists(data_directory):
            raise CommandError(f"The directory {data_directory} does not exist.")

        json_files = [f for f in os.listdir(data_directory) if f.endswith('.json')]

        if not json_files:
            self.stdout.write(self.style.WARNING("No JSON files found in the data directory."))
            return

        # Option to delete existing data before import
        confirm = input("Do you want to delete all existing Words and Stacks before importing? (yes/no): ")
        if confirm.lower() == 'yes':
            Word.objects.all().delete()
            Stack.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Deleted all existing Words and Stacks."))
        else:
            self.stdout.write(self.style.NOTICE("Skipped deletion of existing Words and Stacks."))

        total_stacks = 0
        total_words = 0
        skipped_stacks = 0
        skipped_words = 0

        for json_file in json_files:
            json_file_path = os.path.join(data_directory, json_file)
            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    stack_entries = json.load(file)
            except json.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"Error decoding JSON from {json_file}: {e}"))
                skipped_stacks += 1
                continue

            for stack_entry in stack_entries:
                stack_name = stack_entry.get('stack_name')
                words_data = stack_entry.get('words')

                if not stack_name or not words_data:
                    self.stdout.write(self.style.WARNING(f"Skipping stack with missing fields in {json_file}: {stack_entry}"))
                    skipped_stacks += 1
                    continue

                # Ensure the stack has exactly 50 words
                if len(words_data) != 50:
                    self.stdout.write(self.style.WARNING(f"Stack '{stack_name}' in {json_file} does not contain exactly 50 words. Found: {len(words_data)}. Skipping."))
                    skipped_stacks += 1
                    continue

                stack, created = Stack.objects.get_or_create(name=stack_name, defaults={'order': total_stacks + 1})

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created stack: {stack_name}"))
                else:
                    self.stdout.write(self.style.NOTICE(f"Stack '{stack_name}' already exists. Skipping creation."))
                    # If not creating a new stack, skip importing words to avoid duplication
                    continue

                added_words_in_stack = 0
                skipped_words_in_stack = 0

                for word_entry in words_data:
                    german_word = word_entry.get('german')
                    translation = word_entry.get('translation')
                    sentence = word_entry.get('sentence', '')
                    sentence_translation = word_entry.get('sentence_translation', '')

                    if not german_word or not translation:
                        self.stdout.write(self.style.WARNING(f"Skipping word with missing fields in stack '{stack_name}': {word_entry}"))
                        skipped_words += 1
                        skipped_words_in_stack += 1
                        continue

                    if Word.objects.filter(german__iexact=german_word, stack=stack).exists():
                        self.stdout.write(self.style.NOTICE(f"Word '{german_word}' already exists in stack '{stack_name}'. Skipping."))
                        skipped_words += 1
                        skipped_words_in_stack += 1
                        continue

                    Word.objects.create(
                        german=german_word,
                        translation=translation,
                        sentence=sentence,
                        sentence_translation=sentence_translation,
                        stack=stack
                    )
                    self.stdout.write(self.style.SUCCESS(f"Added word: '{german_word}' to stack '{stack_name}'"))
                    total_words += 1
                    added_words_in_stack += 1

                total_stacks += 1
                if skipped_words_in_stack > 0:
                    self.stdout.write(self.style.WARNING(f"Skipped {skipped_words_in_stack} words in stack '{stack_name}'."))

        self.stdout.write(self.style.SUCCESS(f"\nImport completed: {total_words} words added, {total_stacks} stacks created, {skipped_stacks} stacks skipped, {skipped_words} words skipped."))
