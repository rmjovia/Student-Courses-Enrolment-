# supabase_client.py
from supabase import create_client, Client
from django.conf import settings

def get_supabase_client() -> Client:
    """
    Returns a Supabase client instance.
    This function is called when needed, not at import time.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    return create_client(url, key)