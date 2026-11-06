"""
OAuth 2.0 Authenticator for YouTube Data API v3.
"""

import os
import json
import socket
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Allow local HTTP callback for OAuth development
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from .config import (
    CLIENT_SECRET_FILE,
    TOKEN_FILE,
    YOUTUBE_SCOPES,
    REDIRECT_PORT,
    REDIRECT_PATH,
    REDIRECT_URI
)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Temporary local HTTP handler for OAuth callback at /auth/youtube/callback."""

    flow: Optional[Flow] = None
    auth_code: Optional[str] = None
    last_path: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        OAuthCallbackHandler.last_path = self.path
        parsed = urlparse(self.path)
        if parsed.path == REDIRECT_PATH:
            query = parse_qs(parsed.query)
            if "code" in query:
                OAuthCallbackHandler.auth_code = query["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>AutoReelStudio — YouTube Authorized</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #07090e; color: #f0f4fc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                        .card { background: #0f1624; border: 1px solid #00f0ff; padding: 40px; border-radius: 16px; text-align: center; max-width: 480px; box-shadow: 0 10px 40px rgba(0, 240, 255, 0.2); }
                        h1 { color: #00f0ff; margin-bottom: 12px; }
                        p { color: #8ca2c4; font-size: 15px; line-height: 1.5; }
                        .badge { display: inline-block; background: rgba(0, 255, 163, 0.15); color: #00ffa3; border: 1px solid #00ffa3; padding: 6px 16px; border-radius: 20px; font-weight: 700; margin-top: 15px; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h1>⚡ Authorization Successful!</h1>
                        <p>Your YouTube Channel is now connected to <strong>AutoReelStudio</strong>.</p>
                        <div class="badge">OAuth 2.0 Token Saved</div>
                        <p style="margin-top: 20px; font-size: 13px; color: #536b8e;">You can close this tab and return to the terminal / web studio.</p>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html_content.encode("utf-8"))
            else:
                OAuthCallbackHandler.error = query.get("error", ["Unknown error"])[0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h3>OAuth Authorization Failed: {OAuthCallbackHandler.error}</h3>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress noisy HTTP logs
        return


class YouTubeAuthenticator:
    """Manages Google OAuth 2.0 credentials and YouTube service instantiation."""

    @staticmethod
    def get_credentials() -> Optional[Credentials]:
        """Loads and refreshes OAuth credentials if already present."""
        if not TOKEN_FILE.exists():
            return None

        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), YOUTUBE_SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
            return creds if creds and creds.valid else None
        except Exception as e:
            print(f"⚠️ [YouTubeAuth] Failed loading saved token: {e}")
            return None

    @staticmethod
    def is_authenticated() -> bool:
        """Returns True if valid credentials exist."""
        creds = YouTubeAuthenticator.get_credentials()
        return creds is not None and creds.valid

    @staticmethod
    def create_flow() -> Flow:
        """Initializes OAuth Flow from client_secret.json."""
        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(
                f"Missing {CLIENT_SECRET_FILE}. Please place your Google Cloud OAuth client credentials in {CLIENT_SECRET_FILE}"
            )
        flow = Flow.from_client_secrets_file(
            str(CLIENT_SECRET_FILE),
            scopes=YOUTUBE_SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.autogenerate_code_verifier = False
        flow.code_verifier = None
        return flow

    @staticmethod
    def get_authorization_url() -> Tuple[str, str]:
        """Generates the OAuth URL and state for user consent."""
        flow = YouTubeAuthenticator.create_flow()
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        return auth_url, state

    @classmethod
    def run_local_auth_server(cls, timeout_secs: int = 600) -> Credentials:
        """
        Starts a local HTTP server on port 8000 matching the registered redirect URI,
        prints the authorization link, waits for the user to complete Google OAuth,
        and saves the resulting credentials to youtube_token.json.
        """
        flow = cls.create_flow()
        OAuthCallbackHandler.flow = flow
        OAuthCallbackHandler.auth_code = None
        OAuthCallbackHandler.error = None

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )

        server = HTTPServer(("0.0.0.0", REDIRECT_PORT), OAuthCallbackHandler)
        server.timeout = 2.0

        print("\n" + "=" * 65)
        print("🔑 YOUTUBE DATA API OAUTH 2.0 AUTHORIZATION")
        print("=" * 65)
        print("Please visit the following URL in your browser to authorize AutoReelStudio:")
        print(f"\n👉 {auth_url}\n")
        print(f"Listening on http://localhost:{REDIRECT_PORT}{REDIRECT_PATH} for authorization callback...")
        print("=" * 65)

        import time
        start = time.time()
        while time.time() - start < timeout_secs:
            server.handle_request()
            if OAuthCallbackHandler.auth_code:
                break
            if OAuthCallbackHandler.error:
                server.server_close()
                raise RuntimeError(f"OAuth failed: {OAuthCallbackHandler.error}")

        server.server_close()

        if not OAuthCallbackHandler.auth_code:
            raise TimeoutError("OAuth authorization timed out before callback was received.")

        # Exchange authorization code for token
        try:
            flow.fetch_token(code=OAuthCallbackHandler.auth_code)
        except Exception as ex:
            if OAuthCallbackHandler.last_path:
                full_resp = f"http://localhost:{REDIRECT_PORT}{OAuthCallbackHandler.last_path}"
                flow.fetch_token(authorization_response=full_resp)
            else:
                raise ex
        creds = flow.credentials

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        print("🎉 YouTube credentials successfully authorized and saved to youtube_token.json!")
        return creds

    _bg_auth_thread = None
    _bg_auth_url = None
    _bg_lock = threading.Lock()

    @classmethod
    def get_or_start_auth_url(cls) -> str:
        """
        Ensures a background listener is active on port 8000 and returns
        the exact matching authorization URL with identical PKCE verifier.
        """
        with cls._bg_lock:
            if cls._bg_auth_url and cls._bg_auth_thread and cls._bg_auth_thread.is_alive():
                return cls._bg_auth_url

            flow = cls.create_flow()
            OAuthCallbackHandler.flow = flow
            OAuthCallbackHandler.auth_code = None
            OAuthCallbackHandler.error = None

            auth_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent"
            )
            cls._bg_auth_url = auth_url

            def _listener():
                try:
                    server = HTTPServer(("0.0.0.0", REDIRECT_PORT), OAuthCallbackHandler)
                    server.timeout = 2.0
                    import time
                    start = time.time()
                    while time.time() - start < 1800:  # 30 mins window
                        server.handle_request()
                        if OAuthCallbackHandler.auth_code or OAuthCallbackHandler.error:
                            break
                        if cls.is_authenticated():
                            break
                    server.server_close()
                    if OAuthCallbackHandler.auth_code:
                        try:
                            flow.fetch_token(code=OAuthCallbackHandler.auth_code)
                        except Exception:
                            if OAuthCallbackHandler.last_path:
                                full_resp = f"http://localhost:{REDIRECT_PORT}{OAuthCallbackHandler.last_path}"
                                flow.fetch_token(authorization_response=full_resp)
                        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                            f.write(flow.credentials.to_json())
                        print("\n🎉 YouTube credentials successfully authorized in background listener!")
                except Exception as e:
                    print(f"⚠️ YouTube background auth server note: {e}")

            cls._bg_auth_thread = threading.Thread(target=_listener, daemon=True)
            cls._bg_auth_thread.start()
            return auth_url

    @classmethod
    def get_authenticated_service(cls):
        """Returns the authenticated Google API YouTube v3 client."""
        creds = cls.get_credentials()
        if not creds:
            raise PermissionError(
                "YouTube is not authenticated. Run 'python3 autoreel.py auth-youtube' to connect your channel."
            )
        return build("youtube", "v3", credentials=creds)

    @classmethod
    def get_channel_info(cls) -> Dict[str, Any]:
        """Fetches connected channel metadata and subscriber count."""
        try:
            yt = cls.get_authenticated_service()
            resp = yt.channels().list(mine=True, part="snippet,statistics").execute()
            items = resp.get("items", [])
            if not items:
                return {"authenticated": True, "title": "Unknown Channel", "subscribers": 0}
            chan = items[0]
            snip = chan.get("snippet", {})
            stat = chan.get("statistics", {})
            return {
                "authenticated": True,
                "id": chan.get("id"),
                "title": snip.get("title"),
                "custom_url": snip.get("customUrl"),
                "thumbnail": snip.get("thumbnails", {}).get("default", {}).get("url"),
                "subscribers": int(stat.get("subscriberCount", 0)),
                "video_count": int(stat.get("videoCount", 0)),
                "view_count": int(stat.get("viewCount", 0))
            }
        except Exception as e:
            return {"authenticated": False, "error": str(e)}
