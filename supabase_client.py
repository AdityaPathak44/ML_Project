"""
Supabase client helper for saving plank exercise results.

To use this:
1. Install Supabase client: pip install supabase
2. Set environment variables:
   - SUPABASE_URL: Your Supabase project URL
   - SUPABASE_KEY: Your Supabase project API key (anon/service role)

Example usage:
    from supabase_client import save_plank_result
    save_plank_result(user_id="user123", exercise="Plank", duration_seconds=45.2, timestamp="2024-01-01T12:00:00")
"""

import os
from datetime import datetime

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    print("Warning: Supabase client not installed. Install with: pip install supabase")
    SUPABASE_AVAILABLE = False


def get_supabase_client() -> 'Client':
    """Initialize and return Supabase client."""
    if not SUPABASE_AVAILABLE:
        raise ImportError("Supabase client not available. Install with: pip install supabase")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
    
    return create_client(url, key)


def save_plank_result(user_id: str, exercise: str, duration_seconds: float, timestamp: str = None, table_name: str = "exercise_sessions"):
    """
    Save plank exercise result to Supabase.
    
    Args:
        user_id: Identifier for the user
        exercise: Exercise type (e.g., "Plank")
        duration_seconds: Duration of the plank in seconds
        timestamp: ISO timestamp string (defaults to current UTC time)
        table_name: Name of the table to insert into
    
    Returns:
        dict: Response from Supabase insert operation
        
    Raises:
        Exception: If Supabase operation fails
    """
    if not SUPABASE_AVAILABLE:
        print("Supabase not available. Result not saved.")
        return None
    
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    
    client = get_supabase_client()
    
    data = {
        "user_id": user_id,
        "exercise": exercise,
        "duration_seconds": duration_seconds,
        "timestamp": timestamp,
        "metadata": {
            "exercise_type": "duration_based",
            "source": "web_plank_counter"
        }
    }
    
    try:
        response = client.table(table_name).insert(data).execute()
        print(f"Saved plank result: {user_id}, {exercise}, {duration_seconds}s")
        return response
    except Exception as e:
        print(f"Failed to save to Supabase: {e}")
        raise


def test_connection():
    """Test the Supabase connection."""
    try:
        client = get_supabase_client()
        # Try a simple query to test connection
        response = client.table("exercise_sessions").select("*").limit(1).execute()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test the connection
    test_connection()
    
    # Example usage
    try:
        save_plank_result(
            user_id="test_user",
            exercise="Plank",
            duration_seconds=30.5,
            timestamp=datetime.utcnow().isoformat()
        )
        print("✅ Test insert successful")
    except Exception as e:
        print(f"❌ Test insert failed: {e}")
