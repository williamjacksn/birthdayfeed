import os


class Config:
    log_format: str
    log_level: str
    version: str

    def __init__(self):
        self.log_format = os.getenv('LOG_FORMAT', '%(levelname)s [%(name)s] %(message)s')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.version = os.getenv('APP_VERSION', 'unknown')
