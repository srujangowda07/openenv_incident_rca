import os

def find_non_ascii(directory):
    for root, dirs, files in os.walk(directory):
        if '.git' in root or '__pycache__' in root or '.venv' in root:
            continue
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for i, char in enumerate(content):
                        if ord(char) > 127:
                            print(f"Found non-ASCII character '{char}' (U+{ord(char):04X}) in {path} at position {i}")
            except (UnicodeDecodeError, PermissionError):
                continue

if __name__ == "__main__":
    find_non_ascii('.')
