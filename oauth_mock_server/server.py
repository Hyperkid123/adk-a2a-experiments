from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import secrets
import time
import random
import uvicorn
import asyncio

app = FastAPI(title="OAuth Mock Server")

# Mock data storage
tokens: Dict[str, Dict[str, Any]] = {}

# Simple mock users list
mock_users = [
    {"id": 1, "username": "alice.johnson", "email": "alice.johnson@example.com", "name": "Alice Johnson"},
    {"id": 2, "username": "bob.smith", "email": "bob.smith@example.com", "name": "Bob Smith"},
    {"id": 3, "username": "carol.williams", "email": "carol.williams@example.com", "name": "Carol Williams"},
    {"id": 4, "username": "david.brown", "email": "david.brown@example.com", "name": "David Brown"},
    {"id": 5, "username": "eve.davis", "email": "eve.davis@example.com", "name": "Eve Davis"},
    {"id": 6, "username": "frank.miller", "email": "frank.miller@example.com", "name": "Frank Miller"},
    {"id": 7, "username": "grace.wilson", "email": "grace.wilson@example.com", "name": "Grace Wilson"},
    {"id": 8, "username": "henry.moore", "email": "henry.moore@example.com", "name": "Henry Moore"},
    {"id": 9, "username": "ivy.taylor", "email": "ivy.taylor@example.com", "name": "Ivy Taylor"},
    {"id": 10, "username": "jack.anderson", "email": "jack.anderson@example.com", "name": "Jack Anderson"}
]

# Pydantic models
class TokenRequest(BaseModel):
    grant_type: str
    client_id: Optional[str] = None
    scope: Optional[str] = None

class TokenExchangeRequest(BaseModel):
    grant_type: str = "urn:ietf:params:oauth:grant-type:token-exchange"
    subject_token: str
    subject_token_type: str = "urn:ietf:params:oauth:token-type:access_token"
    requested_token_type: Optional[str] = "urn:ietf:params:oauth:token-type:access_token"
    scope: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: Optional[str] = None

class TokenIntrospectionRequest(BaseModel):
    token: str
    token_type_hint: Optional[str] = None

class TokenIntrospectionResponse(BaseModel):
    active: bool
    scope: Optional[str] = None
    client_id: Optional[str] = None
    exp: Optional[int] = None
    sub: Optional[str] = None
    # Custom fields for user information
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "OK", "service": "OAuth Mock Server"}

@app.post("/token", response_model=TokenResponse)
async def get_token(request: TokenRequest):
    """OAuth 2.0 Token Endpoint - Returns token with randomized user info"""
    if request.grant_type not in ["client_credentials", "authorization_code"]:
        raise HTTPException(status_code=400, detail=f"Unsupported grant_type: {request.grant_type}")

    # Generate random token and pick random user
    access_token = secrets.token_urlsafe(32)
    user = random.choice(mock_users)
    expires_in = 3600

    # For demo purposes, give some users admin privileges
    if user["username"] in ["alice.johnson", "grace.wilson"]:
        scope = request.scope or "user admin"
    else:
        scope = request.scope or "user"

    # Store token data
    tokens[access_token] = {
        "user": user,
        "scope": scope,
        "expires_at": time.time() + expires_in,
        "created_at": time.time()
    }

    return TokenResponse(access_token=access_token, expires_in=expires_in, scope=scope)

@app.post("/token-exchange", response_model=TokenResponse)
async def exchange_token(request: TokenExchangeRequest):
    """OAuth 2.0 Token Exchange Endpoint (RFC 8693)"""
    if request.grant_type != "urn:ietf:params:oauth:grant-type:token-exchange":
        raise HTTPException(status_code=400, detail="Invalid grant_type for token exchange")

    # Validate the subject token
    if request.subject_token not in tokens:
        raise HTTPException(status_code=401, detail="Invalid subject_token")

    subject_token_data = tokens[request.subject_token]
    if subject_token_data["expires_at"] <= time.time():
        raise HTTPException(status_code=401, detail="Expired subject_token")

    # Generate new token
    new_access_token = secrets.token_urlsafe(32)
    expires_in = 3600
    new_scope = request.scope or subject_token_data["scope"]

    tokens[new_access_token] = {
        "user": subject_token_data["user"],
        "scope": new_scope,
        "expires_at": time.time() + expires_in,
        "created_at": time.time()
    }

    return TokenResponse(access_token=new_access_token, expires_in=expires_in, scope=new_scope)

@app.post("/introspect", response_model=TokenIntrospectionResponse)
async def introspect_token(request: TokenIntrospectionRequest):
    """OAuth 2.0 Token Introspection Endpoint (RFC 7662)"""
    token = request.token

    # Check if token exists and is not expired
    if token not in tokens:
        return TokenIntrospectionResponse(active=False)

    token_data = tokens[token]
    if token_data["expires_at"] <= time.time():
        return TokenIntrospectionResponse(active=False)

    # Return token info including user details
    user_info = token_data["user"]
    return TokenIntrospectionResponse(
        active=True,
        scope=token_data["scope"],
        client_id="test-client",  # Static for mock
        exp=int(token_data["expires_at"]),
        sub=str(user_info["id"]),
        username=user_info["username"],
        email=user_info["email"],
        name=user_info.get("name", user_info["username"])
    )

# Async server function for integration with main.py
async def run_oauth_server_async(host: str = "127.0.0.1", port: int = 8003):
    """Run OAuth server as async task"""
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
