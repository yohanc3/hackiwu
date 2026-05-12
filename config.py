import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_env_variable(name: str) -> str:
    value = os.environ.get(name)

    # Panic and exit the program if not all .env vars are there.
    if not value:
        print(f"Panic: Environment variable '{name}' is missing or empty. Please check your .env file and ensure all required variables are set.")
        sys.exit(1)

    return value

# Required Configuration
SUPABASE_URL = get_env_variable("SUPABASE_URL")
SUPABASE_KEY = get_env_variable("SUPABASE_KEY")
FLASK_SECRET_KEY = get_env_variable("FLASK_SECRET_KEY")
