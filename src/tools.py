"""
Tool schemas và execution layer cho trợ lý tra cứu, đặt lịch bác sĩ.

Các hàm trong file trả về chuỗi JSON để MCP Server có thể đóng gói thành
phản hồi JSON-RPC 2.0.
"""

import json
import unicodedata
from typing import Any, Dict


TOOLS_SCHEMA = [
    {
        "name": "doctor_query",
        "description": (
            "Tra cứu thông tin bác sĩ theo tên hoặc chuyên khoa, gồm họ tên, "
            "chuyên khoa, học hàm/học vị và cơ sở làm việc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_name": {
                    "type": "string",
                    "description": "Tên đầy đủ hoặc một phần tên bác sĩ."
                },
                "specialty": {
                    "type": "string",
                    "description": "Chuyên khoa cần tìm, ví dụ: Da liễu."
                }
            },
            "additionalProperties": False
        }
    },
    {
        "name": "doctor_schedule_query",
        "description": "Tra cứu các khung giờ khám còn trống của một bác sĩ trong ngày.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_name": {
                    "type": "string",
                    "description": "Tên bác sĩ cần tra cứu lịch làm việc."
                },
                "date": {
                    "type": "string",
                    "description": "Ngày khám theo định dạng DD/MM/YYYY."
                }
            },
            "required": ["doctor_name", "date"],
            "additionalProperties": False
        }
    },
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch khám cho bệnh nhân với bác sĩ tại một khung giờ còn trống.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Mã bệnh nhân, ví dụ: BN2026001."
                },
                "doctor_name": {
                    "type": "string",
                    "description": "Tên bác sĩ bệnh nhân muốn đặt lịch."
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian khám, định dạng HH:MM DD/MM/YYYY."
                },
                "reason": {
                    "type": "string",
                    "description": "Lý do khám hoặc triệu chứng chính."
                }
            },
            "required": ["patient_id", "doctor_name", "datetime_str"],
            "additionalProperties": False
        }
    },
    {
        "name": "patient_appointment_query",
        "description": "Tra cứu các lịch khám đã đặt theo mã bệnh nhân.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Mã bệnh nhân cần tra cứu, ví dụ: BN2026001."
                }
            },
            "required": ["patient_id"],
            "additionalProperties": False
        }
    }
]


DOCTORS = {
    "BS001": {
        "doctor_name": "PGS.TS Nguyễn Văn A",
        "specialty": "Da liễu",
        "facility": "Bệnh viện Đa khoa Quốc tế Vinmec Times City",
        "available_slots": {
            "15/09/2026": ["09:00", "10:00", "14:00"],
            "16/09/2026": ["08:30", "10:30", "15:00"]
        }
    },
    "BS002": {
        "doctor_name": "ThS.BS Trần Thị B",
        "specialty": "Da liễu",
        "facility": "Bệnh viện Đa khoa Quốc tế Vinmec Central Park",
        "available_slots": {
            "15/09/2026": ["08:00", "13:30", "16:00"]
        }
    },
    "BS003": {
        "doctor_name": "TS.BS Lê Minh C",
        "specialty": "Tim mạch",
        "facility": "Bệnh viện Đa khoa Quốc tế Vinmec Times City",
        "available_slots": {
            "15/09/2026": ["08:30", "11:00", "15:30"]
        }
    }
}

PATIENTS = {
    "BN2026001": {"full_name": "Nguyễn Văn An"},
    "BN2026002": {"full_name": "Trần Thị Bình"}
}

APPOINTMENTS = []


def _json_response(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _normalize_text(value: str) -> str:
    """So khớp thân thiện với tên tiếng Việt có hoặc không có dấu."""
    decomposed = unicodedata.normalize("NFD", value.strip().casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").replace("đ", "d")


def _find_doctors(doctor_name: str = "", specialty: str = "") -> list:
    name_keyword = _normalize_text(doctor_name)
    specialty_keyword = _normalize_text(specialty)
    return [
        {"doctor_id": doctor_id, **doctor}
        for doctor_id, doctor in DOCTORS.items()
        if (not name_keyword or name_keyword in _normalize_text(doctor["doctor_name"]))
        and (not specialty_keyword or specialty_keyword in _normalize_text(doctor["specialty"]))
    ]


def execute_doctor_query(doctor_name: str = "", specialty: str = "") -> str:
    """Tra cứu bác sĩ theo tên và/hoặc chuyên khoa."""
    if not doctor_name.strip() and not specialty.strip():
        doctors = [{"doctor_id": key, **value} for key, value in DOCTORS.items()]
    else:
        doctors = _find_doctors(doctor_name, specialty)

    if not doctors:
        return _json_response({
            "status": "NOT_FOUND",
            "message": "Không tìm thấy bác sĩ phù hợp với thông tin tra cứu."
        })

    # Lịch trống được cung cấp qua doctor_schedule_query, không trả lặp ở đây.
    doctor_profiles = [
        {key: value for key, value in doctor.items() if key != "available_slots"}
        for doctor in doctors
    ]
    return _json_response({
        "status": "SUCCESS",
        "count": len(doctor_profiles),
        "data": doctor_profiles
    })


def execute_doctor_schedule_query(doctor_name: str, date: str) -> str:
    """Tra cứu giờ khám còn trống của bác sĩ trong một ngày."""
    doctors = _find_doctors(doctor_name=doctor_name)
    if not doctors:
        return _json_response({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy bác sĩ '{doctor_name}'."
        })

    doctor = doctors[0]
    slots = doctor["available_slots"].get(date.strip(), [])
    return _json_response({
        "status": "SUCCESS",
        "doctor_id": doctor["doctor_id"],
        "doctor_name": doctor["doctor_name"],
        "date": date.strip(),
        "available_slots": slots,
        "message": (
            f"Bác sĩ còn {len(slots)} khung giờ trống trong ngày {date.strip()}."
            if slots else f"Bác sĩ không còn lịch trống trong ngày {date.strip()}."
        )
    })


def execute_schedule_appointment(
    patient_id: str,
    doctor_name: str,
    datetime_str: str,
    reason: str = ""
) -> str:
    """Đặt lịch nếu bệnh nhân tồn tại và khung giờ của bác sĩ còn trống."""
    normalized_patient_id = patient_id.strip().upper()
    patient = PATIENTS.get(normalized_patient_id)
    if not patient:
        return _json_response({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy bệnh nhân có mã '{normalized_patient_id}'."
        })

    doctors = _find_doctors(doctor_name=doctor_name)
    if not doctors:
        return _json_response({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy bác sĩ '{doctor_name}'."
        })

    try:
        time_value, date_value = datetime_str.strip().split(maxsplit=1)
    except ValueError:
        return _json_response({
            "status": "INVALID_ARGUMENT",
            "message": "Thời gian phải có định dạng HH:MM DD/MM/YYYY."
        })

    doctor = doctors[0]
    slots = doctor["available_slots"].get(date_value, [])
    if time_value not in slots:
        return _json_response({
            "status": "SLOT_UNAVAILABLE",
            "doctor_name": doctor["doctor_name"],
            "requested_datetime": datetime_str.strip(),
            "available_slots": slots,
            "message": "Khung giờ yêu cầu không còn trống; chưa tạo lịch hẹn."
        })

    booking_id = f"VM-{len(APPOINTMENTS) + 1:04d}"
    appointment = {
        "booking_id": booking_id,
        "patient_id": normalized_patient_id,
        "patient_name": patient["full_name"],
        "doctor_id": doctor["doctor_id"],
        "doctor_name": doctor["doctor_name"],
        "specialty": doctor["specialty"],
        "datetime": f"{time_value} {date_value}",
        "reason": reason.strip(),
        "status": "CONFIRMED"
    }
    APPOINTMENTS.append(appointment)
    slots.remove(time_value)

    return _json_response({
        "status": "SUCCESS",
        "data": appointment,
        "message": (
            f"Đặt lịch thành công cho {patient['full_name']} với "
            f"{doctor['doctor_name']} vào {time_value} ngày {date_value}."
        )
    })


def execute_patient_appointment_query(patient_id: str) -> str:
    """Tra cứu lịch khám đã đặt của bệnh nhân."""
    normalized_patient_id = patient_id.strip().upper()
    if normalized_patient_id not in PATIENTS:
        return _json_response({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy bệnh nhân có mã '{normalized_patient_id}'."
        })

    appointments = [
        item for item in APPOINTMENTS if item["patient_id"] == normalized_patient_id
    ]
    return _json_response({
        "status": "SUCCESS",
        "patient_id": normalized_patient_id,
        "patient_name": PATIENTS[normalized_patient_id]["full_name"],
        "count": len(appointments),
        "appointments": appointments,
        "message": f"Tìm thấy {len(appointments)} lịch khám của bệnh nhân."
    })


TOOL_ROUTER = {
    "doctor_query": execute_doctor_query,
    "doctor_schedule_query": execute_doctor_schedule_query,
    "schedule_appointment": execute_schedule_appointment,
    "patient_appointment_query": execute_patient_appointment_query
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Kiểm tra và chuyển lời gọi tới đúng hàm thực thi tool."""
    tool = TOOL_ROUTER.get(tool_name)
    if tool is None:
        return _json_response({
            "status": "UNKNOWN_TOOL",
            "error": f"Tool '{tool_name}' không tồn tại."
        })

    if not isinstance(arguments, dict):
        return _json_response({
            "status": "INVALID_ARGUMENT",
            "error": "arguments phải là một JSON object."
        })

    try:
        return tool(**arguments)
    except TypeError as exc:
        return _json_response({"status": "INVALID_ARGUMENT", "error": str(exc)})
    except Exception as exc:
        return _json_response({"status": "EXECUTION_ERROR", "error": str(exc)})
