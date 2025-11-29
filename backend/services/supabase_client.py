import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # anon key for client-side
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # service role key for server-side

supabase: Client = None
supabase_admin: Client = None


def get_supabase() -> Client:
    """Get Supabase client with anon key (respects RLS)."""
    global supabase
    if supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase


def get_supabase_admin() -> Client:
    """Get Supabase client with service role key (bypasses RLS)."""
    global supabase_admin
    if supabase_admin is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return supabase_admin


def get_supabase_with_token(access_token: str) -> Client:
    """Get Supabase client authenticated with user's access token."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.auth.set_session(access_token, "")
    return client
