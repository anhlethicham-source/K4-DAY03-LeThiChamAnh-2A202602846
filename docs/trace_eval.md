# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** [Le Thi Cham Anh]
> **Mã Học viên:** [2A202602846]
> **Chủ đề Lựa chọn:** [Trợ lý Tư vấn Sức khỏe Vinmec: Tra cứu lịch làm việc bác sĩ chuyên khoa và đặt lịch khám bệnh.]

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- |:--------------:| :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Agent phải tra lịch, đánh giá slot còn trống rồi mới đặt lịch. |
| **2. Tool Interaction** | 5 / 5 | Agent dùng MCP tools để đọc dữ liệu bác sĩ, lịch trống và tạo lịch hẹn. |
| **3. Dynamic Decision** | 5 / 5 | Hành động đặt lịch phụ thuộc trực tiếp vào Observation của bước tra lịch. |
| **4. Long Horizon Goal** | 3 / 5 | Agent giữ mục tiêu đặt khám qua nhiều bước, nhưng mỗi phiên tương đối ngắn. |
| **TỔNG ĐIỂM AGENTIC FIT** | **17 / 20** | Bài toán phù hợp triển khai Agentic System. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
{
  "query": "Đặt lịch khám da liễu cho bệnh nhân BN2026001 với PGS.TS Nguyễn Văn A lúc 10:00 ngày 15/09/2026.",
  "actions": [
    {
      "step": 1,
      "action_type": "TOOL_EXECUTION",
      "thought": "OpenAI quyết định gọi công cụ 'doctor_schedule_query' để kiểm tra lịch trống của bác sĩ trước khi đặt lịch.",
      "tool_name": "doctor_schedule_query",
      "arguments": {
        "doctor_name": "PGS.TS Nguyễn Văn A",
        "date": "15/09/2026"
      },
      "observation": {
        "status": "SUCCESS",
        "doctor_id": "BS001",
        "doctor_name": "PGS.TS Nguyễn Văn A",
        "date": "15/09/2026",
        "available_slots": ["09:00", "10:00", "14:00"],
        "message": "Bác sĩ còn 3 khung giờ trống trong ngày 15/09/2026."
      },
      "llm_latency_ms": 1179.75,
      "tool_latency_ms": 0.08,
      "latency_ms": 1179.83
    },
    {
      "step": 2,
      "action_type": "TOOL_EXECUTION",
      "thought": "OpenAI quyết định gọi công cụ 'schedule_appointment' để tiến hành đặt lịch khám cho bệnh nhân vào khung giờ 10:00 đã được xác nhận là còn trống.",
      "tool_name": "schedule_appointment",
      "arguments": {
        "patient_id": "BN2026001",
        "doctor_name": "PGS.TS Nguyễn Văn A",
        "datetime_str": "10:00 15/09/2026",
        "reason": "Khám da liễu"
      },
      "observation": {
        "status": "SUCCESS",
        "data": {
          "booking_id": "VM-0001",
          "patient_id": "BN2026001",
          "patient_name": "Nguyễn Văn An",
          "doctor_id": "BS001",
          "doctor_name": "PGS.TS Nguyễn Văn A",
          "specialty": "Da liễu",
          "datetime": "10:00 15/09/2026",
          "reason": "Khám da liễu",
          "status": "CONFIRMED"
        },
        "message": "Đặt lịch thành công cho Nguyễn Văn An với PGS.TS Nguyễn Văn A vào 10:00 ngày 15/09/2026."
      },
      "llm_latency_ms": 4014.15,
      "tool_latency_ms": 0.11,
      "latency_ms": 4014.26
    },
    {
      "step": 3,
      "action_type": "FINAL_ANSWER",
      "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
      "output": "Lịch khám da liễu cho bệnh nhân BN2026001 đã được đặt thành công với PGS.TS Nguyễn Văn A vào lúc 10:00 ngày 15/09/2026. Thông tin chi tiết như sau:\n\n- Tên bệnh nhân: Nguyễn Văn An\n- Tên bác sĩ: PGS.TS Nguyễn Văn A\n- Chuyên khoa: Da liễu\n- Thời gian khám: 10:00 ngày 15/09/2026\n- Trạng thái: Đặt lịch thành công\n\nNếu bạn cần thêm thông tin nào khác, hãy cho tôi biết!",
      "latency_ms": 1602.45
    }
  ],
  "total_latency_ms": 6796.54
}
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** __5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** _6__ lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
