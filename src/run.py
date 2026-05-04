from src.read_raw import read_log
from src.parse_envelope import parse_line, parse_event
from src.insert_db import insert_event

lines = read_log("data/auth.log")

total = 0
parsed = 0
inserted = 0

for line in lines:
  total += 1

  envelope = parse_line(line)
  event = parse_event(envelope)

  if event is not None:
    parsed += 1
    success = insert_event(event)
    if success:
      inserted += 1

print(f"Total lines: {total}")
print(f"Parsed events: {parsed}")
print(f"Inserted events: {inserted}")
