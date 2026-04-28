from src.read_raw import read_log
from src.parse_envelope import parse_line, parse_event

lines = read_log("data/auth.log")

for line in lines[:10]:
    envelope = parse_line(line)
    event = parse_event(envelope)

    if event is not None:
        print(event)
