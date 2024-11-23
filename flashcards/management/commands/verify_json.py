import json
import os

def verify_word_count(file_path, expected_count=50):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for stack in data:
        count = len(stack['words'])
        if count != expected_count:
            print(f"Stack '{stack['stack_name']}' in {file_path} has {count} words (expected {expected_count}).")
        else:
            print(f"Stack '{stack['stack_name']}' in {file_path} is correctly formatted with {expected_count} words.")

# Directory containing JSON files
data_directory = 'flashcards/data/'

for filename in os.listdir(data_directory):
    if filename.endswith('.json'):
        filepath = os.path.join(data_directory, filename)
        verify_word_count(filepath)
