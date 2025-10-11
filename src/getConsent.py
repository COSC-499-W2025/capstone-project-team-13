import os

# Ask user for consent
print("This application would like to access your data and computer files.")
print("Please respond with 'allow' or 'don't allow'")

while True:
    response = input("\nYour choice: ").strip().lower()
    
    if response in ['allow', 'don\'t allow', 'dont allow']:
        consent = response.replace('dont', 'don\'t')
        break
    else:
        print("Invalid response. Please type 'allow' or 'don't allow'")

# Store user's response
if consent == 'allow':
    print("Access granted. The application can now proceed.")
else:
    print("Access denied. The application will not access your data.")