import asyncio
import os
import sys

# Thêm thư mục gốc vào PYTHONPATH để import được app.*
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from app.nlp.ai.openai_client import OpenAiClient

async def test_streaming_gpt5():
    client = OpenAiClient()
    print(f"--- Đang test với model: {client.model_name} ---")
    
    prompt = "Xin chào"
    print(f"User: {prompt}\nBot: ", end="", flush=True)
    
    try:
        # Test hàm stream cơ bản
        has_content = False
        async for chunk in client.handle_general_conversation_stream(prompt, []):
            print(chunk, end="", flush=True)
            has_content = True
        
        print("\n\n--- Trạng thái: OK ---")
        if not has_content:
            print("Cảnh báo: Không nhận được dữ liệu stream nào.")
            
    except Exception as e:
        print(f"\n\n--- Lỗi phát sinh: {e} ---")

if __name__ == "__main__":
    asyncio.run(test_streaming_gpt5())
