import json
import os

def remove_duplicates_and_trim(file_path, expected_count=50):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}")
            return

    for stack in data:
        unique_words = {}
        for word in stack['words']:
            german_word = word['german'].strip().lower()
            if german_word not in unique_words:
                unique_words[german_word] = word
        # Assign only unique words
        stack['words'] = list(unique_words.values())[:expected_count]

        # Check if we have exactly 50 words
        if len(stack['words']) != expected_count:
            print(f"Stack '{stack['stack_name']}' in {file_path} has {len(stack['words'])} unique words after trimming.")

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Processed {os.path.basename(file_path)} successfully.")

def main():
    # Define the data directory
    data_directory = os.path.join(os.path.dirname(__file__), 'flashcards', 'data')

    if not os.path.exists(data_directory):
        print(f"The data directory {data_directory} does not exist.")
        return

    # List all JSON files in the data directory
    json_files = [f for f in os.listdir(data_directory) if f.endswith('.json')]

    if not json_files:
        print("No JSON files found in the data directory.")
        return

    # Process each JSON file
    for json_file in json_files:
        file_path = os.path.join(data_directory, json_file)
        remove_duplicates_and_trim(file_path)

if __name__ == '__main__':
    main()
