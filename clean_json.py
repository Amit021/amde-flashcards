import json
import os


def remove_duplicates_and_trim(file_path, assigned_words, expected_count=50):
    """
    Processes a single JSON file to remove duplicate German words across all stacks and trims each stack.

    Parameters:
    - file_path (str): Path to the JSON file to process.
    - assigned_words (set): A global set of already assigned German words.
    - expected_count (int): The maximum number of unique words per stack.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {file_path}: {e}")
            return

    # Process each stack in the JSON file
    for stack in data:
        unique_words = {}
        # Remove duplicates within the stack
        for word in stack.get("words", []):
            german_word = word.get("german", "").strip().lower()
            if german_word and german_word not in unique_words:
                unique_words[german_word] = word

        # Filter out words that have already been assigned globally
        filtered_words = []
        for german_word, word_obj in unique_words.items():
            if german_word not in assigned_words:
                filtered_words.append(word_obj)
                assigned_words.add(german_word)
                if len(filtered_words) == expected_count:
                    break  # Stop if the expected count is reached

        # Assign the filtered list to the stack
        stack["words"] = filtered_words

        # Check if the stack meets the expected count
        if len(stack["words"]) < expected_count:
            print(f"Warning: Stack '{stack.get('stack_name', 'Unnamed Stack')}' in '{os.path.basename(file_path)}' has only {len(stack['words'])} unique words after processing.")

    # Optional: Backup the original file before writing
    backup_path = f"{file_path}.backup"
    try:
        if not os.path.exists(backup_path):
            with open(backup_path, "w", encoding="utf-8") as backup_file:
                json.dump(data, backup_file, ensure_ascii=False, indent=4)
            print(f"Backup created at '{backup_path}'.")
    except Exception as e:
        print(f"Failed to create backup for '{file_path}': {e}")
        return

    # Write the updated data back to the JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Processed '{os.path.basename(file_path)}' successfully.")


def main():
    """
    Main function to process all JSON files in the data directory, ensuring global uniqueness of German words.
    """
    # Define the data directory relative to the script's location
    data_directory = os.path.join(os.path.dirname(__file__), "flashcards", "data")

    if not os.path.exists(data_directory):
        print(f"Error: The data directory '{data_directory}' does not exist.")
        return

    # List all JSON files in the data directory, sorted for consistent processing order
    json_files = sorted([f for f in os.listdir(data_directory) if f.endswith(".json")])

    if not json_files:
        print(f"No JSON files found in the data directory '{data_directory}'.")
        return

    # Initialize a global set to keep track of assigned German words
    assigned_words = set()

    # Optionally, load previously assigned words from a file to persist across runs
    # Uncomment the following lines if you have a 'assigned_words.json' file
    # assigned_words_file = os.path.join(data_directory, 'assigned_words.json')
    # if os.path.exists(assigned_words_file):
    #     with open(assigned_words_file, 'r', encoding='utf-8') as awf:
    #         try:
    #             assigned_words = set(json.load(awf))
    #             print(f"Loaded {len(assigned_words)} previously assigned words.")
    #         except json.JSONDecodeError as e:
    #             print(f"Error loading assigned words from '{assigned_words_file}': {e}")

    # Process each JSON file
    for json_file in json_files:
        file_path = os.path.join(data_directory, json_file)
        remove_duplicates_and_trim(file_path, assigned_words)

    # Optionally, save the updated assigned words to a file for future runs
    # Uncomment the following lines if you want to persist the assigned words
    # with open(assigned_words_file, 'w', encoding='utf-8') as awf:
    #     json.dump(list(assigned_words), awf, ensure_ascii=False, indent=4)
    #     print(f"Assigned words saved to '{assigned_words_file}'.")


if __name__ == "__main__":
    main()
