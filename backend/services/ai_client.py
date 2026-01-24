"""
Unified AI model client for all endpoint calls
"""

import aiohttp
import asyncio
from typing import Optional
from config import Config
from utils.logger import logger


class AIModelClient:
    """
    Unified client for making calls to AI model endpoints
    Supports Telus OpenAI-compatible gateway endpoints
    """
    
    @staticmethod
    async def call_model(
        endpoint: str,
        token: str,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        use_chat: bool = True
    ) -> str:
        """
        Make async call to AI model endpoint with retry logic
        
        Args:
            endpoint: Model endpoint URL
            token: Authentication token
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            system_prompt: Optional system/instruction prompt
            max_retries: Number of retry attempts on failure
        
        Returns:
            Generated text response from model
        """
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Construct messages for chat completions format
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Construct payload - NO MODEL FIELD for Telus gateway
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if use_chat:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            url = f"{endpoint}/v1/chat/completions"
        else:
            payload = {
                "model": "gpt-oss-120b",
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            url = f"{endpoint}/v1/completions"
        
        # Retry loop
        for attempt in range(max_retries):
            try:
                # Disable SSL verification for internal APIs
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.post(
                        url,  # Use chat/completions endpoint
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            # Extract text from chat completion response
                            if use_chat:
                                text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            else:
                                text = data.get("choices", [{}])[0].get("text", "")
                            
                            if text:
                                logger.info(f"✅ Model call successful ({len(text)} chars)")
                                return text
                            else:
                                logger.warning("⚠️  Empty response from model")
                                
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"❌ Model API error: {response.status} - {error_text[:200]}"
                            )
                
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except aiohttp.ClientError as e:
                logger.error(f"🔌 Connection error: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(f"💥 Unexpected error: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        logger.error(f"❌ All {max_retries} attempts failed")
        return ""
    
    @staticmethod
    async def call_gemma(
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = Config.TEMPERATURE_EVENT_INTELLIGENCE,
        max_tokens: int = Config.MAX_TOKENS_EVENT_INTELLIGENCE
    ) -> str:
        """
        Call Gemma-3-27b model
        Used for: Event Intelligence (query parsing)
        """
        return await AIModelClient.call_model(
            endpoint=Config.GEMMA_ENDPOINT,
            token=Config.GEMMA_TOKEN,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    @staticmethod
    async def call_deepseek(
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = Config.TEMPERATURE_WEB_INTELLIGENCE,
        max_tokens: int = Config.MAX_TOKENS_WEB_INTELLIGENCE
    ) -> str:
        """
        Call DeepSeek-v3-2 model
        Used for: Web Intelligence (data aggregation)
        """
        return await AIModelClient.call_model(
            endpoint=Config.DEEPSEEK_ENDPOINT,
            token=Config.DEEPSEEK_TOKEN,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    @staticmethod
    async def call_gpt(
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = Config.TEMPERATURE_GEOSPATIAL_REASONING,
        max_tokens: int = Config.MAX_TOKENS_GEOSPATIAL_REASONING
    ) -> str:
        """
        Call GPT-OSS-120b model
        Used for: Geospatial Reasoning (impact analysis)
        """
        return await AIModelClient.call_model(
            endpoint=Config.GPT_ENDPOINT,
            token=Config.GPT_TOKEN,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            use_chat=False
        )
    
    @staticmethod
    async def call_qwen_coder(
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """
        Call Qwen3Coder-30b model
        Used for: Code generation and technical tasks
        """
        return await AIModelClient.call_model(
            endpoint=Config.QWEN_CODER_ENDPOINT,
            token=Config.QWEN_CODER_TOKEN,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )