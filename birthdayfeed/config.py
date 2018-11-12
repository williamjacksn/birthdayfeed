import os
import pathlib


class Config:
    log_format: str
    log_level: str

    def __init__(self):
        self.log_format = os.getenv('LOG_FORMAT', '%(levelname)s [%(name)s] %(message)s')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')

    @property
    def version(self) -> str:
        """Read version from Dockerfile"""
        dockerfile = pathlib.Path(__file__).resolve().parent.parent / 'Dockerfile'
        with open(dockerfile) as f:
            for line in f:
                if 'org.label-schema.version' in line:
                    return line.strip().split('=', maxsplit=1)[1]
        return 'unknown'
