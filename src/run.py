from src.read_raw import read_log
from src.parse_envelope import parse_line, parse_event
from src.insert_db import insert_event

lines = read_log("data/auth.log")

for line in lines:
  envelope = parse_line(line)
  event = parse_event(envelope)

  if event is not None:
      insert_event(event)
