import json
import pathlib

THIS_FILE = pathlib.PurePosixPath(
    pathlib.Path(__file__).relative_to(pathlib.Path().resolve())
)
CONTAINER_IMAGE = "ghcr.io/williamjacksn/birthdayfeed"
ACTIONS_CHECKOUT = {"name": "Check out repository", "uses": "actions/checkout@v5"}


def gen(content: dict, target: str):
    pathlib.Path(target).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(target).write_text(
        json.dumps(content, indent=2, sort_keys=True), newline="\n"
    )


def gen_compose():
    target = "compose.yaml"
    content = {
        "services": {
            "app": {
                "image": CONTAINER_IMAGE,
                "init": True,
                "ports": ["8080:8080"],
                "volumes": ["./:/app"],
            },
            "shell": {
                "entrypoint": ["/bin/bash"],
                "image": CONTAINER_IMAGE,
                "init": True,
                "volumes": ["./:/app"],
            },
        }
    }
    gen(content, target)


def gen_dependabot(target: str):
    def update(ecosystem: str) -> dict:
        return {
            "package-ecosystem": ecosystem,
            "allow": [{"dependency-type": "all"}],
            "directory": "/",
            "schedule": {"interval": "daily"},
        }

    ecosystems = ["docker", "github-actions", "uv"]
    content = {
        "version": 2,
        "updates": [update(e) for e in ecosystems],
    }

    gen(content, target)


def gen_deploy_workflow():
    target = ".github/workflows/build-and-deploy.yaml"
    content = {
        "name": "Build and deploy app",
        "on": {
            "pull_request": {"branches": ["master"]},
            "push": {"branches": ["master"]},
            "workflow_dispatch": {},
        },
        "permissions": {},
        "env": {
            "description": f"This workflow ({target}) was generated from {THIS_FILE}",
        },
        "jobs": {
            "build": {
                "name": "Build the container image",
                "permissions": {"packages": "write"},
                "runs-on": "ubuntu-latest",
                "steps": [
                    {
                        "name": "Set up Docker Buildx",
                        "uses": "docker/setup-buildx-action@v3",
                    },
                    {
                        "name": "Build the container image",
                        "uses": "docker/build-push-action@v6",
                        "with": {
                            "cache-from": "type=gha",
                            "cache-to": "type=gha,mode=max",
                            "tags": f"{CONTAINER_IMAGE}:latest",
                        },
                    },
                    {
                        "name": "Log in to GitHub container registry",
                        "if": "github.event_name == 'push' || github.event_name == 'workflow_dispatch'",
                        "uses": "docker/login-action@v3",
                        "with": {
                            "password": "${{ github.token }}",
                            "registry": "ghcr.io",
                            "username": "${{ github.actor }}",
                        },
                    },
                    {
                        "name": "Push latest image to registry",
                        "if": "github.event_name == 'push' || github.event_name == 'workflow_dispatch'",
                        "uses": "docker/build-push-action@v6",
                        "with": {
                            "cache-from": "type=gha",
                            "push": True,
                            "tags": f"{CONTAINER_IMAGE}:latest",
                        },
                    },
                ],
            },
            "deploy": {
                "name": "Deploy the app",
                "needs": "build",
                "if": "github.event_name == 'push' || github.event_name == 'workflow_dispatch'",
                "runs-on": "ubuntu-latest",
                "steps": [
                    ACTIONS_CHECKOUT,
                    {
                        "name": "Deploy the app",
                        "run": "sh ci/ssh-deploy.sh",
                        "env": {
                            "SSH_HOST": "${{ secrets.ssh_host }}",
                            "SSH_PRIVATE_KEY": "${{ secrets.ssh_private_key }}",
                            "SSH_USER": "${{ secrets.ssh_user }}",
                        },
                    },
                ],
            },
        },
    }
    gen(content, target)


def gen_ruff_workflow():
    target = ".github/workflows/ruff.yaml"
    content = {
        "name": "Ruff",
        "on": {
            "pull_request": {"branches": ["master"]},
            "push": {"branches": ["master"]},
        },
        "permissions": {"contents": "read"},
        "env": {
            "description": f"This workflow ({target}) was generated from {THIS_FILE}",
        },
        "jobs": {
            "ruff": {
                "name": "Run ruff linting and formatting checks",
                "runs-on": "ubuntu-latest",
                "steps": [
                    ACTIONS_CHECKOUT,
                    {
                        "name": "Run ruff check",
                        "uses": "astral-sh/ruff-action@v3",
                        "with": {"args": "check --output-format=github"},
                    },
                    {
                        "name": "Run ruff format",
                        "uses": "astral-sh/ruff-action@v3",
                        "with": {"args": "format --check"},
                    },
                ],
            }
        },
    }
    gen(content, target)


def main():
    gen_compose()
    gen_dependabot(".github/dependabot.yaml")
    gen_deploy_workflow()
    gen_ruff_workflow()


if __name__ == "__main__":
    main()
