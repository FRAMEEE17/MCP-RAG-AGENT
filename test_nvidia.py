import asyncio
from src.common.config import config
from src.llm.providers.nvidia import NVIDIAProvider

async def test_nvidia():
    # Create the provider
    provider = NVIDIAProvider("nvidia/llama-3.1-nemotron-ultra-253b-v1")
    
    # Define messages
    messages = [
        {"role": "system", "content": "You are an AI assistant with detailed thinking capabilities."},
        {"role": "user", "content": "Explain the process of mcp in detail"}
    ]
    
    # Call the model
    try:
        result = await provider.complete(messages)
        print("Response:")
        print(result["content"])
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_nvidia())