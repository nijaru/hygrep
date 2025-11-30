from pathlib import Path

fn walk(root: Path) raises -> List[Path]:
    var all_files = List[Path]()
    # Use a stack for iterative DFS to avoid recursion limits
    var stack = List[Path]()
    stack.append(root)

    while len(stack) > 0:
        # Pop from the end (efficient)
        var current = stack.pop()
        
        if current.is_dir():
            # listdir returns List[Path]
            var entries = current.listdir()
            for entry in entries:
                if entry[].is_dir():
                     # Check for hidden directories (simple check)
                    if not entry[].name.startswith("."):
                        stack.append(entry[])
                else:
                    all_files.append(entry[])
        else:
            # If the root itself is a file
            all_files.append(current)
            
    return all_files
