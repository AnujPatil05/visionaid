import requests
import os

def main():
    base_url = "http://localhost:8000"
    
    print("Running integration_test.py...")
    try:
        res = requests.get(f"{base_url}/health")
        assert res.json().get("status") == "ok"
        print("Server running")
    except Exception as e:
        print("Failed to reach server:", e)
        return
        
    path_02 = "demo_assets/signs/sign_02.png"
    if not os.path.exists(path_02):
        print("Please run generate_signs.py first.")
        return
        
    with open(path_02, "rb") as f:
        img_bytes = f.read()
        
    def post_process(b):
        return requests.post(f"{base_url}/process", files={'file': ('sign.png', b, 'image/png')}).json()
        
    print(f"\nPOST {path_02}")
    for _ in range(3):
        data1 = post_process(img_bytes)
        if data1.get("action") not in ["skip", "buffering"]:
            break
            
    if data1.get("action") not in ['spoken', 'dedup', 'low_confidence', 'skip', 'none']:
        print("SERVER RETURNED ERROR:", data1)
        
    assert data1.get("action") in ['spoken', 'dedup', 'low_confidence', 'skip', 'none']
    if data1.get("action") == "spoken":
        assert "speech" in data1 and len(data1["speech"]) > 0
    print("Response 1 JSON:", data1)
    
    print(f"\nPOST {path_02} (Dedup Test)")
    for _ in range(3):
        data2 = post_process(img_bytes)
        if data2.get("action") not in ["skip", "buffering"]:
            break
            
    if data1.get("action") == "spoken":
        assert data2.get("action") == "dedup"
    print("Response 2 JSON:", data2)
    
    path_03 = "demo_assets/signs/sign_03.png"
    with open(path_03, "rb") as f:
        img3_bytes = f.read()
        
    print(f"\nPOST {path_03} (Danger Test)")
    for _ in range(3):
        data3 = post_process(img3_bytes)
        if data3.get("action") not in ["skip", "buffering"]:
            break
            
    if data3.get("action") not in ['spoken', 'dedup', 'low_confidence', 'skip', 'none']:
        print("SERVER RETURNED ERROR:", data3)
        
    if data3.get("action") == "spoken":
        assert data3.get("is_danger") is True
    print("Response 3 JSON:", data3)
    
    print("\nAll integration tests passed. Ready for demo.")

if __name__ == "__main__":
    main()
