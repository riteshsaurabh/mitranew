print("Testing environment...")

# Test importing core packages
try:
    import pandas as pd
    import requests
    print("✅ Pandas and Requests imported successfully")
except Exception as e:
    print(f"❌ Error importing pandas/requests: {e}")

# Test creating basic dataframe
try:
    df = pd.DataFrame({'A': [1, 2, 3]})
    print("✅ DataFrame created successfully")
    print(df)
except Exception as e:
    print(f"❌ Error creating dataframe: {e}")

# Test basic HTTP request
try:
    response = requests.get("https://www.google.com")
    print(f"✅ HTTP request successful (status code: {response.status_code})")
except Exception as e:
    print(f"❌ Error making HTTP request: {e}")

print("\nEnvironment test completed") 