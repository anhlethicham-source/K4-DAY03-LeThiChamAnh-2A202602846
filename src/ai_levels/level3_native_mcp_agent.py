"""
📚 [REFERENCE ONLY / CODE MẪU THAM KHẢO]
🧠 CẤP ĐỘ 3: NATIVE MCP AGENT (Native Tool Calling + MCP Server Integration)
⚠️ Lưu ý: File này chỉ dùng để đọc tham khảo kiến trúc. Không chỉnh sửa hay debug file này.
"""

def run_level3_demo():
    print("=== DEMO CẤP ĐỘ 3: NATIVE MCP AGENT ===")
    user_goal = "Tra cứu lịch trống của bác sĩ Nguyễn Văn A ngày 15/09/2026"
    print(f"🎯 Goal: {user_goal}")
    print("🧠 [Thought]: Cần gọi doctor_schedule_query để lấy dữ liệu thời gian thực.")
    print("🛠️ [Native Tool Call]: doctor_schedule_query({'doctor_name': 'Nguyễn Văn A', 'date': '15/09/2026'})")
    print("👁️ [MCP Observation]: {'status': 'SUCCESS', 'available_slots': ['09:00', '14:00']}")
    print("🏁 [Final Answer]: Bác sĩ còn lịch lúc 09:00 và 14:00 ngày 15/09/2026.")

if __name__ == "__main__":
    run_level3_demo()
