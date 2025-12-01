from pathlib import Path
from src.scanner.walker import hyper_scan
from collections import List
from python import Python
import sys

fn main() raises:
    var root_str = "."
    if len(sys.argv()) > 1:
        root_str = sys.argv()[1]
    
    var root = Path(root_str)
    print("Benchmarking Scanner on: " + root_str)
    
    # Use Python for timing (Reliable)
    var py_time = Python.import_module("time")
    var start = py_time.time()
    
    # Run with a catch-all regex to just measure walking + file open overhead
    var files = hyper_scan(root, ".*")
    
    var end = py_time.time()
    
    # Convert PythonObject to Float64
    var start_f = Float64(start)
    var end_f = Float64(end)
    var duration = end_f - start_f
    
    var count = len(files)
    
    var files_per_sec: Float64 = 0.0
    if duration > 0:
        files_per_sec = Float64(count) / duration
    
    print("------------------------------------------------")
    print("Found: " + String(count) + " files")
    print("Time:  " + String(duration) + " seconds")
    print("Speed: " + String(files_per_sec) + " files/sec")
    print("------------------------------------------------")