import base64
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from fastapi import Header, HTTPException
from app.core.config import settings

# Default fallback user ID matching seeded database user
DEFAULT_FALLBACK_USER_ID = "2685f73e-0891-407c-bdf2-01de1e8468c7"


def get_supabase_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header.",
        )

    access_token = authorization.replace("Bearer ", "", 1).strip()

    # Seamlessly handle local / dev / demo tokens
    if access_token.startswith("local_") or access_token.startswith("demo_") or access_token == "demo-token":
        try:
            raw_payload = access_token.split("_", 1)[1]
            decoded = json.loads(base64.b64decode(raw_payload).decode("utf-8"))
            user_id = decoded.get("id") or DEFAULT_FALLBACK_USER_ID
            email = decoded.get("email") or "farmer@rootwise.com"
            full_name = decoded.get("fullName") or "Farmer"
            return {
                "id": user_id,
                "email": email,
                "user_metadata": {"full_name": full_name},
            }
        except Exception:
            return {
                "id": DEFAULT_FALLBACK_USER_ID,
                "email": "farmer@rootwise.com",
                "user_metadata": {"full_name": "Farmer"},
            }

    request = Request(
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Authorization": f"Bearer {access_token}",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            user = json.loads(response.read().decode("utf-8"))

        if not user.get("id"):
            raise HTTPException(
                status_code=401,
                detail="Invalid Supabase user.",
            )

        return user

    except (HTTPError, URLError, TimeoutError):
        # Fallback to local default user if Supabase is unreachable or unconfirmed
        return {
            "id": DEFAULT_FALLBACK_USER_ID,
            "email": "farmer@rootwise.com",
            "user_metadata": {"full_name": "Farmer"},
        }


def get_verified_supabase_user(authorization: str = Header(...)):
    """Fail closed for new APIs that write or reveal owner-scoped M2 data."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header.")

    access_token = authorization.removeprefix("Bearer ").strip()
    if not access_token:
        raise HTTPException(status_code=401, detail="Missing access token.")

    if not settings.SUPABASE_URL or not settings.SUPABASE_PUBLISHABLE_KEY:
        raise HTTPException(status_code=503, detail="Supabase authentication is not configured.")

    request = Request(
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Authorization": f"Bearer {access_token}",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            user = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise HTTPException(status_code=401, detail="Invalid Supabase access token.") from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=503, detail="Supabase authentication is unavailable.") from exc

    if not user.get("id"):
        raise HTTPException(status_code=401, detail="Invalid Supabase user.")

    return user
