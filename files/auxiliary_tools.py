import time

def load_lines(file_path):
    return open(file_path, 'r').read().split('\n')

def get_ms_time():  
    return round(time.time() * 1000)