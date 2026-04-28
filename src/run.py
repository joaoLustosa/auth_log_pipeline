from src.read_raw import read_log

lines = read_log('data/auth.log')

for line in lines[:5]:
    print(line)
