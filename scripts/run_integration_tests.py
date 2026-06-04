import asyncio
import os
import re
import sys
import logging # Added import
from dotenv import load_dotenv
load_dotenv()
from app.chatbot.dialog_manager import DialogManager
from app.core.logger import setup_logging

# Cấu hình logging để ghi vào file thay vì in console bị chồng lấn
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='run_tests.log', 
    filemode='w'
)

# Test cases (23 cases)
TEST_INPUTS_FILE = "test_inputs.txt"

async def run_integration_tests():
    # Khởi tạo logger cơ bản để thấy tiến trình
    setup_logging()
    
    # Đọc trực tiếp các test cases siêu khó từ file .txt của người dùng
    test_cases = []
    try:
        with open("test_inputs.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Kịch bản test là những dòng bắt đầu bằng dấu blockquote '>'
                if line.startswith(">") and len(line) > 5:
                    # Cắt dấu > và dấu nháy kép
                    content = line[1:].strip().strip('"')
                    test_cases.append(content)
    except Exception as e:
        print("Lỗi đọc file:", e)
        # Fallback 1 case nếu lỗi
        test_cases = ["Max 2x + 3y, điều kiện x+y<=10"]
    
    print("="*60)
    print("BẮT ĐẦU CHẠY THỬ NGHIỆM CHATBOT BACKEND (NLP & SOLVER)")
    print("="*60)
    
    dm = DialogManager(user_id="test_runner_bot")
    
    with open("test_results.md", "w", encoding="utf-8") as f:
        f.write("# KẾT QUẢ CHẠY TEST (NLP & SOLVERS)\n\n")
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n[Đang xử lý Case {i}...] User: {text}")
            dm.reset_state() # Đảm bảo mỗi case độc lập
            
            response = await dm.handle_message(text)
            
            # In ra Terminal
            print(f"--> Bot Trả Lời: {response.get('text_response')[:150]}...\n")
            
            # Nếu có logs của parser trả về (thường dùng để debug), ta in ra để theo dõi
            if "logs" in response:
                print(f"  [Logs của parser]: {response['logs']}")
            
            # Ghi vào File báo cáo
            f.write(f"## Case {i}\n")
            f.write(f"**Người dùng:** {text}\n\n")
            f.write(f"**Chatbot:**\n{response.get('text_response')}\n\n")
            
            if response.get("plot_image_base64"):
                f.write(f"> Báo cáo: Chatbot CÓ khởi tạo lệnh vẽ Đồ Thị thành công!\n\n")
            
            if response.get("suggestions"):
                f.write(f"**Gợi ý:** {', '.join(response.get('suggestions'))}\n\n")
                
            f.write("---\n")
            
    print("\n" + "="*60)
    print("ĐÃ CHẠY XONG! Toàn bộ kết quả chi tiết đã được lưu vào file `test_results.md`.")
    print("="*60)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_integration_tests())
