"""Client for pushing data to Exist.io API."""

import requests
from datetime import datetime
from typing import List, Optional

from config import (
    EXIST_ACCESS_TOKEN,
    EXIST_API_BASE,
    EXIST_SCREEN_TIME_ATTR,
    EXIST_SOCIAL_ATTR,
    EXIST_GPT_ATTR,
    EXIST_FOCUS_SCORE_ATTR,
)

# All attributes we manage
MANAGED_ATTRIBUTES = [
    {
        "name": EXIST_SCREEN_TIME_ATTR,
        "label": "Screen Time",
        "group": "productivity",
        "value_type": 3,  # Period in minutes
    },
    {
        "name": EXIST_SOCIAL_ATTR,
        "label": "Social Networks",
        "group": "social",
        "value_type": 3,  # Period in minutes
    },
    {
        "name": EXIST_GPT_ATTR,
        "label": "AI Assistants",
        "group": "productivity",
        "value_type": 3,  # Period in minutes
    },
    {
        "name": EXIST_FOCUS_SCORE_ATTR,
        "label": "Focus Score",
        "group": "productivity",
        "value_type": 0,  # Integer (0-100 scale)
    },
]


def get_headers() -> dict:
    """Get authorization headers for Exist.io API."""
    return {
        "Authorization": f"Bearer {EXIST_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }


def get_user_profile() -> dict:
    """Get the authenticated user's profile."""
    response = requests.get(
        f"{EXIST_API_BASE}/accounts/profile/",
        headers=get_headers()
    )
    response.raise_for_status()
    return response.json()


def get_attributes() -> List[dict]:
    """Get all attributes for the user."""
    response = requests.get(
        f"{EXIST_API_BASE}/attributes/",
        headers=get_headers()
    )
    response.raise_for_status()
    return response.json()


def get_owned_attributes() -> List[dict]:
    """Get attributes owned by our service."""
    response = requests.get(
        f"{EXIST_API_BASE}/attributes/owned/",
        headers=get_headers()
    )
    response.raise_for_status()
    return response.json()


def create_attribute(
    name: str,
    label: str,
    group: str = "productivity",
    value_type: int = 3,  # Period (minutes)
    manual: bool = False
) -> dict:
    """
    Create a new custom attribute.
    
    Args:
        name: Attribute name (lowercase, no spaces)
        label: User-facing label
        group: Group name (activity, productivity, etc.)
        value_type: 0=integer, 1=float, 3=period(minutes)
        manual: Whether this is a manual entry attribute
    """
    response = requests.post(
        f"{EXIST_API_BASE}/attributes/create/",
        headers=get_headers(),
        json=[{
            "name": name,
            "label": label,
            "group": group,
            "value_type": value_type,
            "manual": manual
        }]
    )
    response.raise_for_status()
    return response.json()


def acquire_attribute(name: str) -> dict:
    """
    Acquire ownership of an attribute to write to it.
    
    This must be done before updating values.
    """
    response = requests.post(
        f"{EXIST_API_BASE}/attributes/acquire/",
        headers=get_headers(),
        json=[{"name": name}]
    )
    response.raise_for_status()
    return response.json()


def update_attribute(name: str, date: str, value: int) -> dict:
    """
    Update an attribute's value for a specific date.
    
    Args:
        name: Attribute name
        date: Date in YYYY-MM-DD format
        value: The value to set
    """
    response = requests.post(
        f"{EXIST_API_BASE}/attributes/update/",
        headers=get_headers(),
        json=[{
            "name": name,
            "date": date,
            "value": value
        }]
    )
    response.raise_for_status()
    return response.json()


def ensure_attribute(attr_config: dict) -> bool:
    """
    Ensure an attribute exists and is owned by us.
    
    Args:
        attr_config: Dict with name, label, group, value_type
        
    Returns True if successful.
    """
    name = attr_config["name"]
    
    # First check if we already own it
    try:
        owned = get_owned_attributes()
        results = owned.get("results", []) if isinstance(owned, dict) else owned
        if isinstance(results, list):
            for attr in results:
                if isinstance(attr, dict) and attr.get("name") == name:
                    return True
    except Exception:
        pass
    
    # Try to acquire existing attribute first
    try:
        result = acquire_attribute(name)
        if result.get("success") and len(result["success"]) > 0:
            print(f"  Acquired: {name}")
            return True
        # If failed with not_found, fall through to create
    except requests.exceptions.HTTPError:
        pass
    
    # Create the attribute
    try:
        result = create_attribute(
            name=name,
            label=attr_config["label"],
            group=attr_config["group"],
            value_type=attr_config["value_type"]
        )
        if result.get("failed") and len(result["failed"]) > 0:
            print(f"  Failed to create {name}: {result['failed']}")
            return False
        
        # Now acquire it
        result = acquire_attribute(name)
        if result.get("success") and len(result["success"]) > 0:
            print(f"  Created and acquired: {name}")
            return True
        else:
            print(f"  Failed to acquire {name}: {result}")
            return False
    except requests.exceptions.HTTPError as e:
        print(f"  Error with {name}: {e}")
        if hasattr(e, 'response'):
            print(f"    Response: {e.response.text}")
        return False


def ensure_all_attributes() -> bool:
    """
    Ensure all managed attributes exist and are owned by us.
    
    Returns True if all successful.
    """
    print("Setting up Exist.io attributes...")
    all_ok = True
    for attr_config in MANAGED_ATTRIBUTES:
        if not ensure_attribute(attr_config):
            all_ok = False
    return all_ok


def push_attribute_value(name: str, minutes: int, date: Optional[datetime] = None) -> dict:
    """
    Push an attribute value to Exist.io.
    
    Args:
        name: Attribute name
        minutes: Value in minutes
        date: Date to update (defaults to today)
    """
    if date is None:
        date = datetime.now()
    
    date_str = date.strftime("%Y-%m-%d")
    return update_attribute(name, date_str, minutes)


def push_screen_time(minutes: int, date: Optional[datetime] = None) -> dict:
    """Push screen time value to Exist.io."""
    return push_attribute_value(EXIST_SCREEN_TIME_ATTR, minutes, date)


def push_social_time(minutes: int, date: Optional[datetime] = None) -> dict:
    """Push social networks time value to Exist.io."""
    return push_attribute_value(EXIST_SOCIAL_ATTR, minutes, date)


def push_gpt_time(minutes: int, date: Optional[datetime] = None) -> dict:
    """Push AI/GPT time value to Exist.io."""
    return push_attribute_value(EXIST_GPT_ATTR, minutes, date)


def push_focus_score(score: int, date: Optional[datetime] = None) -> dict:
    """Push focus score (0-100) to Exist.io."""
    return push_attribute_value(EXIST_FOCUS_SCORE_ATTR, score, date)


if __name__ == "__main__":
    # Test the client
    print("Testing Exist.io client...")
    try:
        profile = get_user_profile()
        print(f"Connected as: {profile.get('username', 'Unknown')}")
        print(f"Timezone: {profile.get('timezone', 'Unknown')}")
        
        # Ensure all attributes exist
        print()
        if ensure_all_attributes():
            print("\nAll attributes ready!")
            
            # Show owned attributes
            owned = get_owned_attributes()
            results = owned.get("results", []) if isinstance(owned, dict) else owned
            if isinstance(results, list):
                names = [a.get('name') if isinstance(a, dict) else a for a in results]
                print(f"Owned attributes: {names}")
        else:
            print("\nSome attributes failed to set up")
            
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")
