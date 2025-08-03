# log_generator.py
# written by: David Redmond

import random
import time
from datetime import datetime, timedelta

users = ['ann', 'barry', 'charlie', 'david', 'edward', 'fiona', 'grainne']
files = ['etc/passwd', '/home/ann/report.docx', '/var/log/syslog', ]

#write a function to generate one log line
def generate_log_line(current_time):
    event_type = random.choice(['LOGIN', 'FILEACCESS', 'SYSTEM'])
    level = random.choice(['INFO', 'ERROR'])

    if event_type == 'LOGIN':
        user = random.choice(users)
        status = random.choice(['success', 'failure'])
        return f"{current_time} {level} LOGIN user={user} status={status}"
    elif event_type == 'FILEACCESS':
        user = random.choice(users)
        file_accessed = random.choice(files)
        return f"{current_time} {level} FILEACCESS user={user} file = {file_accessed}"
    else: #system ERROR
        crash_code = random.randint(1000, 9999)
        return f"{current_time} {level} SYSTEM crash_code= {crash_code}"

# generate timestamps that move forward
start_time = datetime.now()

#write the logs to a file
with open('logs/sample.log', 'w') as f:
    current_time = start_time
    for _ in range(100): #generate 100 logs
        current_time += timedelta(seconds=random.randint(1, 30))
        timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
        log_line = generate_log_line(timestamp)
        f.write(log_line + '\n')
