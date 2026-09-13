"""MCP Server mô phỏng cho trợ lý tra cứu và đặt lịch khám bệnh."""

import json
import sys
from typing import Any, Dict, List

from tools import TOOLS_SCHEMA, dispatch_tool_call


if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class MCPMedicalServer:
    """Công bố và thực thi các medical tools qua cấu trúc JSON-RPC 2.0."""

    def __init__(self, server_name: str = "vinmec-medical-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            raw_result = dispatch_tool_call(tool_name, arguments)
            content = json.loads(raw_result)
        except (TypeError, json.JSONDecodeError) as exc:
            content = {"status": "PROTOCOL_ERROR", "error": str(exc)}

        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


# Giữ tương thích với mã cũ trong trường hợp còn import tên lớp này.
MCPAcademicServer = MCPMedicalServer


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ MCP SERVER (vinmec-medical-mcp-server)")
    print("==========================================================")

    server = MCPMedicalServer()
    tools = server.list_tools()
    print(f"✅ MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng tools: {len(tools)}")

    test_result = server.call_tool("doctor_query", {"specialty": "Da liễu"})
    print("✅ Test doctor_query:")
    print(json.dumps(test_result, ensure_ascii=False, indent=2))
