from src.read_raw import read_log
from src.parse_envelope import parse_line

lines = read_log("data/auth.log")

for line in lines[:10]:
    print(parse_line(line))
