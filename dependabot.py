import json
import pathlib

eco = "package-ecosystem"
daily = {"interval": "daily"}

data = {
    "#generator": "dependabot.py",
    "version": 2,
    "enable-beta-ecosystems": True,
    "updates": [
        {eco: "docker", "directory": "/", "schedule": daily},
        {eco: "github-actions", "directory": "/", "schedule": daily},
        {
            eco: "uv",
            "allow": [{"dependency-type": "all"}],
            "directory": "/",
            "schedule": daily,
        },
    ],
}

pathlib.Path(".github/dependabot.yaml").write_text(
    json.dumps(data, indent=2, sort_keys=True)
)
