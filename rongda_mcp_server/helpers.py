"""
Helper functions for the Rongda MCP Server.
"""
from typing import Dict, Any, Optional, Tuple, Union
import aiohttp
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.backends import default_backend


# Default headers for API requests
DEFAULT_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Sec-Fetch-Site': 'same-origin',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Mode': 'cors',
    'Origin': 'https://doc.rongdasoft.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Safari/605.1.15',
    'Sec-Fetch-Dest': 'empty',
    'Priority': 'u=3, i',
    'xp_version': '3941'
}


async def get_public_key_str(session: aiohttp.ClientSession) -> Tuple[str, int]:
    """
    Get the public key from the Rongda API.
    
    Args:
        session: An active aiohttp ClientSession
        
    Returns:
        Dictionary containing the public key and timestamp
        Example: {
            "publicKey": "MIGfMA0GCS...",
            "timestamp": 1745551962582
        }
    """
    # API endpoint
    url = "https://doc.rongdasoft.com/api/user-server/system/getPublicKey"
    
    try:
        # Make the API request
        async with session.post(url, headers=DEFAULT_HEADERS) as response:
            # Check if the request was successful
            if response.status == 200:
                # Parse the JSON response
                data = await response.json()
                
                # Check if the response is valid
                if data.get("code") == 200 and data.get("success") and "data" in data:
                    response_data = data["data"]
                    public_key = response_data.get("publicKey", "")
                    timestamp = response_data.get("timestamp", 0)
                    
                    return public_key, timestamp
                else:
                    print(f"Error: Unexpected API response format: {data}")
                    raise ValueError("Unexpected API response format")
            else:
                # Handle error status
                print(f"Error: API request failed with status code {response.status}")
                raise Exception(f"API request failed with status code {response.status}")
    
    except Exception as e:
        print(f"Error getting public key: {str(e)}")
        raise


def encrypt_with_public_key(data: Union[str, bytes], public_key_str: str, timestamp: int) -> str:
    """
    Encrypt data using the RSA public key with PKCS#1 v1.5 padding.
    Compatible with JS jsencrypt library which uses pkcs1pad2.
    
    Args:
        data: The data to encrypt (string or bytes)
        public_key_str: Base64-encoded public key string from get_public_key_str
        timestamp: The timestamp to be concatenated with the data
        
    Returns:
        Base64-encoded encrypted data string
    """
    # Convert data to string if it's bytes
    if isinstance(data, bytes):
        data_str = data.decode('utf-8')
    else:
        data_str = data
    
    # Concatenate data with timestamp using pipe separator
    combined_data = f"{data_str}|{timestamp}"
    
    try:
        # Decode the Base64-encoded public key string to get DER format
        der_data = base64.b64decode(public_key_str)
        
        # Load the DER-formatted key
        public_key = load_der_public_key(der_data, backend=default_backend())
        
        # Encrypt the combined data with PKCS#1 v1.5 padding (pkcs1pad2)
        encrypted_data = public_key.encrypt(
            combined_data.encode('utf-8'),
            padding.PKCS1v15()
        )
        
        # Return Base64-encoded encrypted data
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    except Exception as e:
        print(f"Encryption error: {str(e)}")
        raise


async def login(username: str, password: str) -> aiohttp.ClientSession:
    """
    Login to the Rongda API using the provided credentials.
    Creates and returns a session with authentication cookies.
    
    Args:
        username: User's login username
        password: User's password in plain text (will be encrypted)
        
    Returns:
        aiohttp ClientSession with authentication cookies and headers set
    """
    # Create a new session
    session = aiohttp.ClientSession()
    
    try:
        # First, get the public key for encryption
        public_key_str, timestamp = await get_public_key_str(session)
        
        # Encrypt password with the retrieved public key and timestamp
        encrypted_password = encrypt_with_public_key(password, public_key_str, timestamp)
        
        # API endpoint for login
        url = "https://doc.rongdasoft.com/api/user-server/system/login"
        
        # Add content type header for form submission
        headers = DEFAULT_HEADERS.copy()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        # Prepare form data
        form_data = {
            'username': username,
            'password': encrypted_password,
            'terminal': 'web'
        }
        
        # Make the login request
        async with session.post(url, headers=headers, data=form_data) as response:
            # Parse the response
            response_data = await response.json()
            
            # Check if login was successful
            if response.status == 200 and response_data.get("code") == 200 and response_data.get("success"):
                print("Login successful")
                # Return the session with cookies already set from the response
                print(f"Session cookies: {session.cookie_jar}")
                print(f"Session headers: {session.headers}")
                print(f"Session response: {response_data}")
                print(f"Session token: {response_data['data']['accessToken']}")
                return session
            else:
                error_msg = response_data.get("msg", "Unknown error")
                print(f"Login failed: {error_msg}")
                # Close the session since login failed
                await session.close()
                raise ValueError(f"Login failed: {error_msg}")
                
    except Exception as e:
        # Make sure to close the session on any error
        await session.close()
        print(f"Login error: {str(e)}")
        raise


if __name__ == "__main__":
    from os import environ
    # Example usage
    async def main():
        try:
            async with (await login(environ["RD_USER"], environ["RD_PASS"])) as session:
                print(f"Login successful, session: {session}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    import asyncio
    asyncio.run(main())