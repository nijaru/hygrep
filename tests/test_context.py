import sys
import os
sys.path.append(os.getcwd()) # Ensure src is found

from src.inference.context import ContextExtractor

def test_extraction():
    extractor = ContextExtractor()
    
    # Create dummy file
    dummy_path = "tests/dummy.py"
    code = (
        "def hello():\n"
        "    print('Hello')\n"
        "\n"
        "class World:\n"
        "    def greet(self):\n"
        "        pass\n"
    )
    
    with open(dummy_path, "w") as f:
        f.write(code)
        
    try:
        blocks = extractor.extract(dummy_path)
        print(f"Found {len(blocks)} blocks:")
        for b in blocks:
            print(f" - {b['type']}: {b['name']} (Lines {b['start_line']}-{b['end_line']})")
            
        assert len(blocks) >= 1
        
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)

if __name__ == "__main__":
    test_extraction()