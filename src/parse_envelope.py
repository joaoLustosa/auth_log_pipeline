import re

def parse_line(line: str) -> dict:
  line = line.strip() # removes \n

  # Splits log
  parts = line.split(" ", 4)

  timestamp = "2024 " + " ".join(parts[0:3]) #Adds a year for the db insertion
  host = parts[3]

  # Separates process and message
  process_part, message = parts[4].split(":", 1)
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

  if "accepted publickey" in msg_lower:
      result["event_type"] = "AUTH"
      result["auth_outcome"] = "SUCCESS"
      result["user_validity"] = "VALID"

      result["user_name"] = extract_user_accepted(msg)
      result["ip"] = extract_ip(msg)

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

  elif "invalid user" in msg_lower:
      result["event_type"] = "AUTH"
      result["auth_outcome"] = "FAILURE"
      result["user_validity"] = "INVALID"
      result["failure_mode"] = "INVALID_USER"

      result["user_name"] = extract_user_invalid(msg)
      result["ip"] = extract_ip(msg)

  if result["event_type"] is None:
    return None

  return result

# Auxiliary extract functions
def extract_user_for(msg):
    match = re.search(r'for ([a-zA-Z0-9._-]+)', msg)
    return match.group(1) if match else None

def extract_user_accepted(msg):
    match = re.search(r'Accepted .* for ([a-zA-Z0-9._-]+)', msg)
    return match.group(1) if match else None

def extract_user_invalid(msg):
    match = re.search(r'Invalid user ([a-zA-Z0-9._-]+)', msg)
    return match.group(1) if match else None

def extract_ip(msg):
    match = re.search(r'from ([0-9a-fA-F:.]+)', msg)
    return match.group(1) if match else None
