"""Bestway Spa API client."""
from __future__ import annotations

import hashlib
import json
import logging
import random
import string
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp
import async_timeout

from .const import (
    API_VISITOR_ENDPOINT,
    API_THING_SHADOW_ENDPOINT,
    API_COMMAND_ENDPOINT,
    HEATER_STATE_OFF,
    HEATER_STATE_HEATING,
    HEATER_STATE_PASSIVE,
)

_LOGGER = logging.getLogger(__name__)

class BestwaySpa:
    """Bestway Spa API client."""

    def __init__(
        self,
        appid: str,
        appsecret: str,
        device_id: str,
        product_id: str,
        registration_id: str,
        visitor_id: str,
        client_id: str,
    ) -> None:
        """Initialize the Bestway Spa client."""
        self._appid = appid
        self._appsecret = appsecret
        self._device_id = device_id
        self._product_id = product_id
        self._registration_id = registration_id
        self._visitor_id = visitor_id
        self._client_id = client_id
        self._token = None
        self._token_expires_at = None
        self._session = None

    @staticmethod
    def _get_random_nonce(n: int) -> str:
        """Generate a random nonce."""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choices(chars, k=n))

    @staticmethod
    def _md5_of_string(input_string: str) -> str:
        """Generate MD5 hash of a string."""
        return hashlib.md5(input_string.encode('utf-8')).hexdigest()

    def _generate_auth_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Generate authentication headers."""
        nonce = self._get_random_nonce(32)
        ts = str(int(time.time()))
        string_to_hash = self._appid + self._appsecret + nonce + ts
        sign = self._md5_of_string(string_to_hash).upper()
        
        headers = {
            'pushtype': 'Android',
            'appid': self._appid,
            'nonce': nonce,
            'ts': ts,
            'accept-language': 'en',
            'sign': sign,
            'Host': 'smarthub-eu.bestwaycorp.com',
            'Connection': 'Keep-Alive',
            'User-Agent': 'okhttp/4.9.0',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        if token:
            headers['Authorization'] = f'token {token}'
        
        return headers

    async def _get_token(self) -> str:
        """Get or refresh the authentication token."""
        if (
            self._token
            and self._token_expires_at
            and datetime.now() < self._token_expires_at
        ):
            return self._token

        headers = self._generate_auth_headers()
        payload = {
            "app_id": self._appid,
            "brand": "",
            "client_id": self._client_id,
            "lan_code": "en",
            "location": "GB",
            "marketing_notification": 0,
            "push_type": "android",
            "registration_id": self._registration_id,
            "timezone": "GMT",
            "visitor_id": self._visitor_id
        }

        async with self._session.post(
            API_VISITOR_ENDPOINT,
            headers=headers,
            json=payload,
            ssl=False
        ) as response:
            if response.status != 200:
                raise Exception("Failed to obtain token")

            data = await response.json()
            token = data.get('data', {}).get('token')
            if not token:
                raise Exception("No token in response")

            self._token = token
            self._token_expires_at = datetime.now() + timedelta(hours=23)
            return token

    async def get_state(self) -> Dict[str, Any]:
        """Get the current state of the spa."""
        if not self._session:
            self._session = aiohttp.ClientSession()

        token = await self._get_token()
        headers = self._generate_auth_headers(token)
        payload = {
            "device_id": self._device_id,
            "product_id": self._product_id
        }

        async with self._session.post(
            API_THING_SHADOW_ENDPOINT,
            headers=headers,
            json=payload,
            ssl=False
        ) as response:
            if response.status != 200:
                raise Exception("Failed to get spa state")

            data = await response.json()
            if data.get('code') == 10001:
                # Token is not authorized, refresh and retry
                self._token = None
                token = await self._get_token()
                headers = self._generate_auth_headers(token)
                async with self._session.post(
                    API_THING_SHADOW_ENDPOINT,
                    headers=headers,
                    json=payload,
                    ssl=False
                ) as retry_response:
                    if retry_response.status != 200:
                        raise Exception("Failed to get spa state after token refresh")
                    data = await retry_response.json()

            if 'data' not in data:
                raise Exception("Invalid response format")

            _LOGGER.debug("Spa state response: %s", data['data'])
            return data['data']

    async def set_state(self, state: str, value: int) -> Dict[str, Any]:
        """Set the state of the spa."""
        if not self._session:
            self._session = aiohttp.ClientSession()

        try:
            # Get current state first
            current_state = await self.get_state()
            _LOGGER.debug("Current state before update: %s", current_state)

            token = await self._get_token()
            headers = self._generate_auth_headers(token)
            
            # Update the state with the correct payload structure
            payload = {
                "device_id": self._device_id,
                "product_id": self._product_id,
                "desired": json.dumps({
                    "state": {
                        "desired": {
                            state: value
                        }
                    }
                })
            }
            
            _LOGGER.debug("Setting state %s to %s with payload: %s", state, value, payload)

            async with self._session.post(
                API_COMMAND_ENDPOINT,
                headers=headers,
                json=payload,
                ssl=False
            ) as response:
                response_text = await response.text()
                _LOGGER.debug("Raw response: %s", response_text)
                
                if response.status != 200:
                    _LOGGER.error("Failed to control spa state. Status: %d, Response: %s", response.status, response_text)
                    raise Exception(f"Failed to control spa state. Status: {response.status}, Response: {response_text}")

                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    _LOGGER.error("Failed to parse response as JSON: %s", str(e))
                    raise Exception(f"Invalid JSON response: {response_text}")

                if data.get('code') == 10001:
                    # Token is not authorized, refresh and retry
                    self._token = None
                    token = await self._get_token()
                    headers = self._generate_auth_headers(token)
                    async with self._session.post(
                        API_COMMAND_ENDPOINT,
                        headers=headers,
                        json=payload,
                        ssl=False
                    ) as retry_response:
                        retry_text = await retry_response.text()
                        _LOGGER.debug("Retry raw response: %s", retry_text)
                        
                        if retry_response.status != 200:
                            _LOGGER.error("Failed to control spa state after token refresh. Status: %d, Response: %s", retry_response.status, retry_text)
                            raise Exception(f"Failed to control spa state after token refresh. Status: {retry_response.status}, Response: {retry_text}")
                        
                        try:
                            data = json.loads(retry_text)
                        except json.JSONDecodeError as e:
                            _LOGGER.error("Failed to parse retry response as JSON: %s", str(e))
                            raise Exception(f"Invalid JSON response on retry: {retry_text}")

                _LOGGER.debug("State update response: %s", data)
                return data

        except Exception as e:
            _LOGGER.error("Error setting state: %s", str(e))
            raise

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None 