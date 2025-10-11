import sys

def request_ai_consent():
    """
    Requests explicit user permission before using external AI/LLM services.
    Explains implications on data privacy and ensures user consent.
    """
    print("=== User Consent Required ===\n")
    print("This software may send text or other inputs (folder, files, etc.) that you provide to external services (ex. LLM).")
    print("\nBy proceeding, you agree that:")
    print(" • Data you provide may be temporarily transmitted to an external AI service for processing.")
    print(" • Data is used solely for analysis or processing within this application.")
    print(" • No personal or identifiable information will be shared beyond this purpose.")
    print(" • You can withdraw consent at any time by exiting the program.\n")
    
    while True:
        consent = input("Do you consent to use external AI/LLM services? (yes/no): ").strip().lower()
        if consent == "yes":
            print("\n Consent granted. Proceeding with analysis...")
            return True
        elif consent == "no":
            print("\n Consent not granted. Exiting program.")
            sys.exit(0)
        else:
            print("Please type 'yes' or 'no'.")

if __name__ == "__main__":
    request_ai_consent()
