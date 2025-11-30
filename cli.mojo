from src.scanner.walker import hyper_scan
from pathlib import Path
import sys

fn main() raises:
    var args = sys.argv()
    if len(args) < 3:
        print("Usage: hygrep <pattern> <path>")
        return

    var pattern = args[1]
    var path_str = args[2]
    var root = Path(path_str)
    
    print("HyperGrep: Searching for '" + pattern + "' in " + path_str)
    
    try:
        var matches = hyper_scan(root, pattern)
        
        print("\n--- Results ---")
        for i in range(len(matches)):
            print(matches[i])
            
        print("\nFound " + String(len(matches)) + " matches.")
    except e:
        print("Error: " + String(e))

