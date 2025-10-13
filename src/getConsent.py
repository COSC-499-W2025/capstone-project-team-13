consent_status = None

def get_user_consent():
    global consent_status
    print("This application would like to access your data and computer files.")
    print("Please respond with 'allow' or 'don't allow'")
    while True:
        response = input("\nYour choice: ").strip().lower()
        if response in ['allow', "don't allow", 'dont allow']:
            consent_status = response.replace('dont', "don't")
            break
        else:
            print("Invalid response. Please type 'allow' or 'don't allow'")
    if consent_status == 'allow':
        print("Access granted. The application can now proceed.")
    else:
        print("Access denied. The application will not access your data.")
    return consent_status

def show_consent_status():
    global consent_status
    if consent_status is None:
        return "Consent not set."
    return f"Current consent status: {consent_status}"