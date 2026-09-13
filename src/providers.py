"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import unicodedata
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return "[Mock Chatbot Response]: Tôi có thể hướng dẫn thông tin chung về dịch vụ khám Vinmec."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        normalized = unicodedata.normalize("NFD", prompt.casefold())
        prompt_lower = "".join(c for c in normalized if unicodedata.category(c) != "Mn").replace("đ", "d")
        patient_match = re.search(r"bn\d+", prompt_lower)
        patient_id = patient_match.group(0).upper() if patient_match else ""

        if "ket qua tool schedule_appointment" in prompt_lower:
            return {
                "type": "text",
                "content": "Đã hoàn tất xử lý yêu cầu đặt lịch khám theo kết quả từ hệ thống.",
                "thought": "Công cụ đặt lịch đã trả kết quả; tổng hợp phản hồi cho bệnh nhân."
            }

        if "ket qua tool doctor_schedule_query" in prompt_lower and "som nhat" in prompt_lower:
            slot_match = re.search(r'"available_slots"\s*:\s*\[\s*"([0-9:]+)"', prompt)
            slot = slot_match.group(1) if slot_match else "09:00"
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"patient_id": patient_id or "BN2026002", "doctor_name": "PGS.TS Nguyễn Văn A", "datetime_str": f"{slot} 15/09/2026", "reason": "Khám da liễu"},
                "thought": "Đã có lịch trống; chọn khung giờ sớm nhất theo yêu cầu."
            }

        if "ket qua tool" in prompt_lower:
            result_match = re.search(r"KẾT QUẢ TOOL [^:]+:\s*(\{.*\})", prompt, re.DOTALL)
            result_text = result_match.group(1) if result_match else "kết quả vừa nhận"
            return {
                "type": "text",
                "content": f"Kết quả từ hệ thống: {result_text}",
                "thought": "Đã có observation từ công cụ; tổng hợp và trả lời người dùng."
            }

        if patient_id and ("lich hen" in prompt_lower or "lich kham" in prompt_lower) and "dat lich" not in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "patient_appointment_query",
                "arguments": {"patient_id": patient_id},
                "thought": "Cần tra cứu lịch khám theo mã bệnh nhân."
            }

        if "som nhat" in prompt_lower and ("lich trong" in prompt_lower or "kiem tra lich" in prompt_lower):
            return {
                "type": "tool_call",
                "tool_name": "doctor_schedule_query",
                "arguments": {"doctor_name": "PGS.TS Nguyễn Văn A", "date": "15/09/2026"},
                "thought": "Cần xem lịch trống trước khi chọn giờ sớm nhất."
            }

        if "dat lich" in prompt_lower and patient_id:
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"patient_id": patient_id, "doctor_name": "PGS.TS Nguyễn Văn A", "datetime_str": "10:00 15/09/2026", "reason": "Khám da liễu"},
                "thought": "Người dùng đã cung cấp đủ thông tin để đặt lịch khám."
            }

        if "lich trong" in prompt_lower or "lich lam viec" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "doctor_schedule_query",
                "arguments": {"doctor_name": "PGS.TS Nguyễn Văn A", "date": "15/09/2026"},
                "thought": "Cần tra cứu lịch trống của bác sĩ."
            }

        if "bac si" in prompt_lower or "da lieu" in prompt_lower:
            arguments = {"doctor_name": "Nguyễn Văn A"} if "nguyen van a" in prompt_lower else {"specialty": "Da liễu"}
            return {
                "type": "tool_call",
                "tool_name": "doctor_query",
                "arguments": arguments,
                "thought": "Cần tra cứu danh mục bác sĩ từ dữ liệu công cụ."
            }

        return {
            "type": "text",
            "content": "Tôi có thể hỗ trợ tra cứu bác sĩ, xem lịch trống và đặt lịch khám Vinmec.",
            "thought": "Câu hỏi chung, không cần gọi công cụ."
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            return {"type": "text", "content": f"Không thể kết nối Gemini API: {str(e)}", "thought": "Live API gặp lỗi; không dùng Mock để tránh tạo bằng chứng nghiệm thu sai."}


class OpenAIProvider(BaseLLMProvider):
    """OpenAI-compatible Provider cho OpenAI hoặc OpenRouter."""
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            return {"type": "text", "content": f"Không thể kết nối OpenAI API: {str(e)}", "thought": "Live API gặp lỗi; không dùng Mock để tránh tạo bằng chứng nghiệm thu sai."}


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if key and key != "your_openrouter_api_key_here":
            return OpenAIProvider(
                api_key=key,
                base_url="https://openrouter.ai/api/v1",
                model=os.getenv("LLM_MODEL") or "openai/gpt-4o-mini"
            )
        return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
