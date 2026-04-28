def parse_line(line: str) -> dict:
  line = line.strip() # removes \n

  # Splits log
  parts = line.split(" ", 4)

  timestamp = " ".join(parts[0:3])
  host = parts[3]

  # Separates process and message
  process_part, message = parts[4].split(":", 1)
  process = process_part.split("[")[0] # Removes PID if present
  raw_message = message.strip()

  return {
    "timestamp": timestamp,
    "host": host,
    "process": process,
    "message": message
  }
