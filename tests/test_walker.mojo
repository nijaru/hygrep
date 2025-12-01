from src.scanner.walker import hyper_scan
from pathlib import Path
from testing import assert_true, TestSuite

fn test_walker_scan() raises:
    var root = Path("src")
    # Scan for "Regex" which appears in c_regex.mojo and walker.mojo
    var results = hyper_scan(root, "Regex")
    
    assert_true(len(results) > 0, "Should find at least one file")
    
    var found_c_regex = False
    for i in range(len(results)):
        var p = results[i]
        if "c_regex.mojo" in String(p):
            found_c_regex = True
            
    assert_true(found_c_regex, "Should find c_regex.mojo")

fn main() raises:
    TestSuite.discover_tests[__functions_in_module()]().run()