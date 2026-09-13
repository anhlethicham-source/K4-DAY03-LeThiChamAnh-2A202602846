"""Ứng dụng CLI cho trợ lý ReAct tra cứu và đặt lịch khám Vinmec."""

import json
import os
import sys
import time

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mcp_server import MCPMedicalServer
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_AGENT_SYSTEM_PROMPT
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ 5 test case của trợ lý bệnh viện."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(base_dir, "config", "test_cases.example.json")
        print("⚠️ Chưa có config/test_cases.json; đang dùng file mẫu.")
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_waterfall_trace(trace_data: list):
    """Ghi chuỗi Thought → Action → Observation → Final Answer."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trace_path = os.path.join(base_dir, "docs", "trace_waterfall.json")
    os.makedirs(os.path.dirname(trace_path), exist_ok=True)
    with open(trace_path, "w", encoding="utf-8") as file:
        json.dump(trace_data, file, ensure_ascii=False, indent=2)
    print(f"📊 Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'.")


def run_baseline_chatbot(user_query: str, provider):
    print(f"\n💬 [CHATBOT BASELINE] {user_query}")
    print(provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT))


def run_react_agent(user_query: str, provider, mcp_server: MCPMedicalServer) -> list:
    """Chạy ReAct nhiều bước; mỗi Observation được đưa lại cho LLM."""
    print(f"\n🤖 [REACT MEDICAL AGENT] {user_query}")
    trace_logs = []
    working_prompt = user_query

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 ReAct Step {step}/{MAX_ITERATIONS} ---")
        started_at = time.perf_counter()
        response = provider.generate_with_tools(
            working_prompt,
            mcp_server.list_tools(),
            system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )
        llm_latency = round((time.perf_counter() - started_at) * 1000, 2)
        thought = response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought] {thought}")

        if response.get("type") == "text":
            content = response.get("content", "")
            print(f"🏁 [Final Answer] {content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": content,
                "latency_ms": llm_latency
            })
            return trace_logs

        if response.get("type") != "tool_call":
            content = "LLM trả về phản hồi không đúng định dạng tool call."
            trace_logs.append({
                "step": step, "query": user_query, "action_type": "ERROR",
                "output": content, "latency_ms": llm_latency
            })
            print(f"⚠️ {content}")
            return trace_logs

        tool_name = response.get("tool_name", "")
        arguments = response.get("arguments", {})
        print(f"🛠️ [Action] {tool_name}({arguments})")
        tool_started_at = time.perf_counter()
        mcp_result = mcp_server.call_tool(tool_name, arguments)
        tool_latency = round((time.perf_counter() - tool_started_at) * 1000, 2)
        observation = mcp_result.get("result", {})
        print(f"👁️ [Observation] {json.dumps(observation, ensure_ascii=False)}")
        trace_logs.append({
            "step": step,
            "query": user_query,
            "action_type": "TOOL_EXECUTION",
            "thought": thought,
            "tool_name": tool_name,
            "arguments": arguments,
            "observation": observation,
            "llm_latency_ms": llm_latency,
            "tool_latency_ms": tool_latency,
            "latency_ms": round(llm_latency + tool_latency, 2)
        })

        working_prompt = (
            f"YÊU CẦU BAN ĐẦU: {user_query}\n\n"
            f"KẾT QUẢ TOOL {tool_name}: {json.dumps(observation, ensure_ascii=False)}\n\n"
            "Hãy tiếp tục giải quyết yêu cầu. Nếu cần tool khác thì gọi tool; "
            "nếu đã đủ dữ liệu thì trả lời người dùng và không gọi lại tool cũ."
        )

    content = "Không thể hoàn tất yêu cầu trong số bước cho phép."
    trace_logs.append({
        "step": MAX_ITERATIONS + 1,
        "query": user_query,
        "action_type": "MAX_ITERATIONS_REACHED",
        "output": content,
        "latency_ms": 0.0
    })
    print(f"⚠️ {content}")
    return trace_logs


def run_test_suite(provider, mcp_server):
    tests = load_test_cases()
    all_traces = []
    completed = 0
    for test in tests:
        print("\n==================================================")
        print(f"🧪 [{test['id']}] {test['type']} — {test['complexity']}")
        print(f"📌 Kỳ vọng: {test['expected_behavior']}")
        if test["question"].strip().startswith("TODO"):
            print("⏸️ Test case chưa được hoàn thiện.")
            continue
        all_traces.extend(run_react_agent(test["question"], provider, mcp_server))
        completed += 1
    print(f"\n📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed}/{len(tests)} test cases.")
    if all_traces:
        save_waterfall_trace(all_traces)


if __name__ == "__main__":
    print("==========================================================")
    print("🏥 VINMEC — TRỢ LÝ TRA CỨU VÀ ĐẶT LỊCH KHÁM")
    print("==========================================================")
    llm_provider = get_llm_provider()
    medical_server = MCPMedicalServer()
    print(f"🔌 LLM Provider: {llm_provider.__class__.__name__}")
    print(f"🌐 MCP Server: {medical_server.server_name}")

    if "--interactive" in sys.argv:
        print("\nGõ 'exit' hoặc 'quit' để kết thúc.")
        while True:
            try:
                query = input("👤 Bệnh nhân hỏi: ").strip()
                if not query or query.casefold() in {"exit", "quit"}:
                    break
                save_waterfall_trace(run_react_agent(query, llm_provider, medical_server))
            except (KeyboardInterrupt, EOFError):
                break
    elif "--all" in sys.argv:
        run_test_suite(llm_provider, medical_server)
    else:
        print("\nCách dùng:")
        print("  python src/app.py --all          Chạy toàn bộ test suite")
        print("  python src/app.py --interactive  Trò chuyện trực tiếp")
