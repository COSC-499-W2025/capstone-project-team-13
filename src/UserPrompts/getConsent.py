from src.UserPrompts.config_integration import request_and_store_basic_consent

def get_user_consent():
    return "allow" if request_and_store_basic_consent() else "don't allow"

