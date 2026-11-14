import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from fastapi import Header, HTTPException
from app.core.config import settings


def get_supabase_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header.",
        )

    access_token = authorization.replace("Bearer ", "", 1)

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

    except HTTPError:
        raise HTTPException(
            status_code=401,
            detail="Supabase authentication failed. Please sign in again.",
        )
    except (URLError, TimeoutError):
        raise HTTPException(
            status_code=503,
            detail="Unable to verify Supabase authentication.",
        )
