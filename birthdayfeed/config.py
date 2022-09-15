import os


class Config:
    version: str
    web_server_threads: int = 8

    def __init__(self):
        self.version = os.getenv('APP_VERSION', 'unknown')
        self.web_server_threads = int(os.getenv('WEB_SERVER_THREADS', '8'))
