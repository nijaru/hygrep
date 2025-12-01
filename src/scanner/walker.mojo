from pathlib import Path
from collections import List
from algorithm import parallelize
from memory import UnsafePointer, alloc
from src.scanner.c_regex import Regex

fn scan_file(file: Path, re: Regex) -> Bool:
    try:
        with open(file, "r") as f:
            var content = f.read()
            return re.matches(content)
    except:
        return False

fn hyper_scan(root: Path, pattern: String) raises -> List[Path]:
    var candidates = List[Path]()
    var all_files = List[Path]()
    
    # 1. Collect files (Single Threaded for now)
    var stack = List[Path]()
    stack.append(root)

    while len(stack) > 0:
        var current = stack.pop()
        if current.is_dir():
            try:
                var entries = current.listdir()
                for i in range(len(entries)):
                    var entry = entries[i]
                    var full_path = current / entry
                    
                    if entry.name().startswith("."):
                        continue
                        
                    if full_path.is_dir():
                        stack.append(full_path)
                    else:
                        # print("Found file: " + String(full_path))
                        all_files.append(full_path)
            except:
                print("Error accessing: " + String(current))
                continue
        else:
            all_files.append(current)

    var num_files = len(all_files)
    print("Scanned " + String(num_files) + " files.")

    if num_files == 0:
        return candidates^

    # 2. Parallel Scan
    var re = Regex(pattern)
    var mask = alloc[Bool](num_files)
    
    @parameter
    fn worker(i: Int):
        if scan_file(all_files[i], re):
            mask[i] = True
        else:
            mask[i] = False

    parallelize[worker](num_files)
    
    # 3. Gather results
    for i in range(num_files):
        if mask[i]:
            candidates.append(all_files[i])
            
    mask.free()
            
    return candidates^