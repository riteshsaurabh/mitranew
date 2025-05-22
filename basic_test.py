print("Starting basic test...")

try:
    import pandas as pd
    print("Successfully imported pandas")
    
    # Create a simple DataFrame
    data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
    df = pd.DataFrame(data)
    print("Created DataFrame:")
    print(df)
    
    print("Basic pandas test completed successfully")
except Exception as e:
    print(f"Error: {str(e)}") 