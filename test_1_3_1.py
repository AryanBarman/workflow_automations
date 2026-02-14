"""
Quick test for Task 1.3.1 - List workflow executions endpoint
"""
import requests

if __name__ == "__main__":
    # Test 1: 404 for non-existent workflow
    print("Test 1: 404 for non-existent workflow")
    response = requests.get("http://localhost:8000/api/workflows/00000000-0000-0000-0000-000000000000/executions")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    print("✅ PASS: Returns 404 for non-existent workflow\n")
    
    # Test 2: 200 for existing workflow (even if no executions)
    print("Test 2: 200 for existing workflow")
    response = requests.get("http://localhost:8000/api/workflows/fdfc6de8-925b-43ea-9d29-4405462e8e24/executions")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print(f"✅ PASS: Returns 200 with {len(data)} executions")
    print(f"Response: {data[:1] if data else '[]'}\n")  # Show first execution
    
    print("All tests passed! ✅")