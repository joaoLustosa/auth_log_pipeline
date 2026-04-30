from datetime import datetime
import re

def parse_line(line: str) -> dict:
  line = line.strip() # removes \n

  parts = line.split()

  timestamp_str = f"2026 {parts[0]} {parts[1]} {parts[2]}" #Adds year for db insertion
  timestamp = datetime.strptime(timestamp_str, "%Y %b %d %H:%M:%S")

  host = parts[3]

  # reconstruct remainder
  rest = " ".join(parts[4:])

  # Separates process and message
  process_part, message = rest.split(":", 1)
  process = process_part.split("[")[0] # Removes PID if present
  raw_message = message.strip()

  return {
    "timestamp": timestamp,
    "host": host,
    "process": process,
    "message": raw_message
  }

def parse_event(envelope):
  msg = envelope["message"]
  msg_lower = msg.lower()

  result = {
      "timestamp": envelope["timestamp"],
      "host": envelope["host"],
      "process": envelope["process"],
      "event_type": None,
      "auth_outcome": None,
      "user_validity": None,
      "failure_mode": None,
      "user_name": None,
      "ip": None,
      "command": None,
      "raw_message": msg
  }

  # SUCCESS
  if "accepted publickey" in msg_lower:
      result["event_type"] = "AUTH"
      result["auth_outcome"] = "SUCCESS"
      result["user_validity"] = "VALID"

      result["user_name"] = extract_user_for(msg)
      result["ip"] = extract_ip(msg)

  # MAX ATTEMPTS
  elif "maximum authentication attempts exceeded" in msg_lower:
    result["event_type"] = "AUTH"
    result["auth_outcome"] = "FAILURE"
    result["failure_mode"] = "MAX_ATTEMPTS"

    if "invalid user" in msg_lower:
        result["user_validity"] = "INVALID"
        result["user_name"] = extract_user_invalid(msg)
    else:
        result["user_validity"] = "VALID"
        result["user_name"] = extract_user_for(msg)

    result["ip"] = extract_ip(msg)

  # PREAUTH INVALID USER (no IP expected)
  elif "input_userauth_request" in msg_lower and "invalid user" in msg_lower:
      result["event_type"] = "AUTH"
      result["auth_outcome"] = "FAILURE"
      result["user_validity"] = "INVALID"
      result["failure_mode"] = "PREAUTH_INVALID_USER"

      result["user_name"] = extract_user_invalid(msg)
      result["ip"] = None

  # GENERIC INVALID USER
  elif "invalid user" in msg_lower:
      result["event_type"] = "AUTH"
      result["auth_outcome"] = "FAILURE"
      result["user_validity"] = "INVALID"
      result["failure_mode"] = "INVALID_USER"

      result["user_name"] = extract_user_invalid(msg)
      result["ip"] = extract_ip(msg)

  if result["event_type"] is None:
    result["event_type"] = "OTHER"

  return result

# Auxiliary extract functions
def extract_user_for(msg):
  match = re.search(r'for ([a-zA-Z0-9._-]+)', msg)
  return match.group(1) if match else None

def extract_user_invalid(msg):
  match = re.search(r'invalid user ([a-zA-Z0-9._-]+)', msg, re.IGNORECASE)
  return match.group(1) if match else None

def extract_ip(msg):
  match = re.search(r'from ([0-9a-fA-F:.]+)', msg)
  return match.group(1) if match else None
