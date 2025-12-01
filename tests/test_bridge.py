import sys
import os
import json
sys.path.append(os.getcwd())

from src.inference.bridge import init_searcher, run_search

def test_bridge():
    model_path = "models/reranker.onnx"
    tok_path = "models/tokenizer.json"
    
    if not os.path.exists(model_path):
        print("Skipping test: models not found")
        return

    print("Initializing searcher...")
    init_searcher(model_path, tok_path)
    
    # Create a dummy file to search
    dummy_file = "tests/bridge_dummy.py"
    with open(dummy_file, "w") as f:
        f.write("def login():\n    # User login logic\n    pass\n\ndef logout():\n    pass\n")
        
    try:
        print("Running search...")
        # Search for "user authentication" to test semantic matching
        res_json = run_search("user authentication", [dummy_file])
        results = json.loads(res_json)
        
        print(f"Got {len(results)} results")
        for r in results:
            print(f" - {r['type']} {r['name']} (Score: {r['score']:.4f})")
            
        assert len(results) > 0
        # 'login' should score higher than 'logout' for 'authentication'
        first = results[0]
        assert first['name'] == 'login'
        
    finally:
        if os.path.exists(dummy_file):
            os.remove(dummy_file)

if __name__ == "__main__":
    test_bridge()
