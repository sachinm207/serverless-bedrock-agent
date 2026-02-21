"""HR Leave Agent — Lambda backend for Bedrock Agent action group."""
import json
from datetime import datetime

# -- mock HR data (in production this would be a database) --

EMPLOYEES = {
    "EMP001": {"name": "Priya Sharma", "team": "engineering", "pto_remaining": 12, "sick_remaining": 5, "role": "Senior Developer"},
    "EMP002": {"name": "James Chen", "team": "engineering", "pto_remaining": 3, "sick_remaining": 5, "role": "DevOps Engineer"},
    "EMP003": {"name": "Sarah Johnson", "team": "marketing", "pto_remaining": 8, "sick_remaining": 4, "role": "Content Manager"},
    "EMP004": {"name": "Raj Patel", "team": "engineering", "pto_remaining": 0, "sick_remaining": 2, "role": "Junior Developer"},
    "EMP005": {"name": "Maria Garcia", "team": "sales", "pto_remaining": 15, "sick_remaining": 5, "role": "Account Executive"},
}

TEAM_CALENDAR = {
    "engineering": {
        "2026-02": [
            {"employee_id": "EMP002", "name": "James Chen", "dates": "Feb 23-25", "type": "PTO"},
        ],
        "2026-03": [
            {"employee_id": "EMP001", "name": "Priya Sharma", "dates": "Mar 9-13", "type": "PTO"},
            {"employee_id": "EMP004", "name": "Raj Patel", "dates": "Mar 16", "type": "Sick"},
        ],
    },
    "marketing": {
        "2026-03": [
            {"employee_id": "EMP003", "name": "Sarah Johnson", "dates": "Mar 2-6", "type": "PTO"},
        ],
    },
    "sales": {
        "2026-03": [
            {"employee_id": "EMP005", "name": "Maria Garcia", "dates": "Mar 10-14", "type": "PTO"},
        ],
    },
}

POLICIES = {
    "pto": (
        "Annual PTO allowance: 20 days for full-time employees, accrued at 1.67 days/month. "
        "Requests of 1-2 days need 3 business days notice. Requests of 3+ days need 2 weeks notice. "
        "Unused PTO carries over up to 5 days into the next calendar year. "
        "No more than 10 consecutive business days without VP approval. Manager approval required for all requests."
    ),
    "sick_leave": (
        "5 sick days per year, no advance notice needed but notify your manager by 9 AM. "
        "Doctor's note required if you're out 3+ consecutive days. Sick days don't carry over."
    ),
    "remote_work": (
        "Up to 2 days/week remote with manager approval. Core hours 10 AM - 4 PM ET. "
        "VPN required for all remote access. Full-time remote needs VP sign-off."
    ),
    "bereavement": (
        "5 paid days for immediate family (spouse, parent, child, sibling). "
        "3 paid days for extended family. Does not count against PTO."
    ),
    "parental": (
        "16 weeks fully paid for primary caregivers, 6 weeks for secondary. "
        "Notify HR at least 30 days before expected start date."
    ),
}


def check_leave_balance(employee_id):
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        return {"error": f"No employee found with ID {employee_id}"}
    return {
        "employee_id": employee_id,
        "name": emp["name"],
        "pto_remaining": emp["pto_remaining"],
        "sick_remaining": emp["sick_remaining"],
        "pto_annual_total": 20,
        "sick_annual_total": 5,
    }


def submit_leave_request(employee_id, start_date, end_date, leave_type):
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        return {"error": f"No employee found with ID {employee_id}"}

    leave_type = leave_type.lower()

    try:
        s = datetime.strptime(start_date, "%Y-%m-%d")
        e = datetime.strptime(end_date, "%Y-%m-%d")
        days = max(1, (e - s).days + 1)
    except ValueError:
        days = 1

    if leave_type in ("pto", "vacation") and emp["pto_remaining"] < days:
        return {
            "status": "denied",
            "reason": f"Not enough PTO. You requested {days} days but only have {emp['pto_remaining']} remaining.",
            "employee_id": employee_id,
        }
    if leave_type in ("sick", "sick_leave") and emp["sick_remaining"] < days:
        return {
            "status": "denied",
            "reason": f"Not enough sick leave. You requested {days} days but only have {emp['sick_remaining']} remaining.",
            "employee_id": employee_id,
        }

    req_id = f"LR-2026-{employee_id[-3:]}-{start_date.replace('-', '')}"
    return {
        "status": "submitted",
        "request_id": req_id,
        "employee_id": employee_id,
        "name": emp["name"],
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "days_requested": days,
        "message": f"Leave request {req_id} submitted for manager approval. Confirmation email within 24 hours.",
    }


def get_company_policy(topic):
    topic_clean = topic.lower().strip().replace(" ", "_")
    for key, text in POLICIES.items():
        if key in topic_clean or topic_clean in key:
            return {"topic": key, "policy": text}
    return {"error": f"No policy found for '{topic}'. Available: {', '.join(POLICIES.keys())}"}


def get_team_calendar(team_name, month):
    team = team_name.lower().strip()
    if team not in TEAM_CALENDAR:
        return {"error": f"Unknown team '{team_name}'. Available: {', '.join(TEAM_CALENDAR.keys())}"}

    cal = TEAM_CALENDAR[team]
    month_map = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }
    ml = month.lower().strip()

    for period, entries in cal.items():
        if ml in period or period in ml:
            return {"team": team_name, "month": period, "out_of_office": entries}
        for name, num in month_map.items():
            if name in ml and num in period:
                return {"team": team_name, "month": period, "out_of_office": entries}

    return {"team": team_name, "month": month, "out_of_office": [], "note": "Nobody scheduled off."}


# -- Lambda entry point --

FUNCTION_MAP = {
    "check_leave_balance": lambda p: check_leave_balance(p.get("employee_id", "")),
    "submit_leave_request": lambda p: submit_leave_request(
        p.get("employee_id", ""), p.get("start_date", ""),
        p.get("end_date", ""), p.get("leave_type", "pto"),
    ),
    "get_company_policy": lambda p: get_company_policy(p.get("topic", "")),
    "get_team_calendar": lambda p: get_team_calendar(p.get("team_name", ""), p.get("month", "")),
}


def lambda_handler(event, context):
    fn = event.get("function", "")
    params = {p["name"]: p["value"] for p in event.get("parameters", [])}

    handler = FUNCTION_MAP.get(fn)
    result = handler(params) if handler else {"error": f"Unknown function: {fn}"}

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "function": fn,
            "functionResponse": {
                "responseBody": {"TEXT": {"body": json.dumps(result)}}
            },
        },
    }
