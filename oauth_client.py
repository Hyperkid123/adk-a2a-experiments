import httpx
import asyncio
from typing import Optional, Dict, Any


class OAuthClient:
    """OAuth client for interacting with our mock OAuth server"""

    def __init__(self, server_url: str = "http://localhost:8003"):
        self.server_url = server_url

    async def get_token(self, grant_type: str = "client_credentials", scope: str = "user") -> Optional[Dict[str, Any]]:
        """Get an access token from the OAuth server"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.server_url}/token",
                    json={
                        "grant_type": grant_type,
                        "scope": scope
                    },
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error getting token: {response.status_code} {response.text}")
                    return None

        except Exception as e:
            print(f"Failed to get token: {e}")
            return None

    async def exchange_token(self, subject_token: str, new_scope: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Exchange an existing token for a new one with potentially different scope"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                data = {
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "subject_token": subject_token,
                    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "requested_token_type": "urn:ietf:params:oauth:token-type:access_token"
                }

                if new_scope:
                    data["scope"] = new_scope

                response = await client.post(
                    f"{self.server_url}/token-exchange",
                    json=data,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error exchanging token: {response.status_code} {response.text}")
                    return None

        except Exception as e:
            print(f"Failed to exchange token: {e}")
            return None

    async def get_oauth_flow_token(self) -> Optional[str]:
        """
        Complete OAuth flow: get initial token, exchange it, return final token
        Simulates real-world OAuth workflow where tokens are exchanged
        """
        print("🔑 Starting OAuth token flow...")

        # Step 1: Get initial token
        print("  📝 Getting initial access token...")
        token_response = await self.get_token(grant_type="client_credentials", scope="user")
        if not token_response:
            print("  ❌ Failed to get initial token")
            return None

        initial_token = token_response["access_token"]
        print(f"  ✅ Got initial token: {initial_token[:20]}...")

        # Step 2: Exchange token (simulating token refinement/scope adjustment)
        print("  🔄 Exchanging token...")
        exchange_response = await self.exchange_token(initial_token, new_scope="user")
        if not exchange_response:
            print("  ❌ Failed to exchange token")
            return None

        final_token = exchange_response["access_token"]
        print(f"  ✅ Got exchanged token: {final_token[:20]}...")
        print("🎉 OAuth flow completed successfully!")

        return final_token