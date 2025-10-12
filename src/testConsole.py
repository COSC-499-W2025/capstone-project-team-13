import os
import sys

# Import functions from getConsent.py
try:
    from getConsent import get_user_consent, show_consent_status  # Example functions
except ImportError:
    print("Could not import functions from getConsent.py. Please check the file and function names.")
    sys.exit(1)

# Simple clear command, specifies by OS
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# Console-based dashboard to test initial functions
def dashboard():
    while True:
        clear_console()
        print("=== Console Testing Dashboard ===")
        print("1. Get User Consent")
        print("2. Show Consent Status")
        print("3. Exit")
        choice = input("Select an option (1-3): ").strip()

        # Basic input selection. Runs corresponding functions when called
        if choice == '1':
            result = get_user_consent()
            print(f"Consent result: {result}")
            input("Press Enter to continue...")
        elif choice == '2':
            status = show_consent_status()
            print(f"Consent status: {status}")
            input("Press Enter to continue...")
        elif choice == '3':
            print("Exiting dashboard.")
            break
        else:
            print("Invalid choice. Try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    dashboard()