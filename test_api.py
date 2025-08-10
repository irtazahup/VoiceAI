import requests
import json

# Test API endpoints
BASE_URL = "http://localhost:8001"

def test_upload():
    print("🧪 Testing File Upload...")
    
    # First login to get token
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code != 200:
            print("❌ Login failed, cannot test upload")
            return
            
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test upload with a dummy text file (simulating audio)
        files = {
            'file': ('test_audio.txt', 'This is a test audio file content', 'text/plain')
        }
        data = {
            'title': 'Test Recording Upload'
        }
        
        response = requests.post(f"{BASE_URL}/upload-recording/", 
                               headers=headers, 
                               files=files, 
                               data=data)
        
        print(f"Upload response: {response.status_code}")
        if response.status_code == 200:
            print("✅ File upload successful!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Upload failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Upload test error: {e}")

def test_api():
    print("🧪 Testing Voice-to-Text API...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print("✅ Server is running - API docs accessible")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        return
    
    # Test 2: Register a new user
    test_user = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=test_user)
        if response.status_code in [200, 201]:
            print("✅ User registration successful")
            user_data = response.json()
            print(f"   User ID: {user_data.get('id')}")
        elif response.status_code == 400 and "already registered" in response.text:
            print("ℹ️  User already exists (expected)")
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    # Test 3: Login
    try:
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            print("✅ User login successful")
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"   Token: {access_token[:20]}...")
            
            # Test 4: Get user info with token
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{BASE_URL}/me", headers=headers)
            if response.status_code == 200:
                print("✅ Authenticated request successful")
                user_info = response.json()
                print(f"   User: {user_info.get('email')}")
            else:
                print(f"❌ Authenticated request failed: {response.status_code}")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    # Test 5: Check CORS headers
    try:
        response = requests.options(f"{BASE_URL}/register", headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        })
        print(f"🔍 CORS preflight response: {response.status_code}")
        if response.status_code == 200:
            print("✅ CORS is properly configured")
        else:
            print("❌ CORS configuration may have issues")
    except Exception as e:
        print(f"❌ CORS test error: {e}")
    
    # Test 6: File upload
    test_upload()

if __name__ == "__main__":
    test_api()
