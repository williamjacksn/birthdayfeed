import gen
import pathlib


build_and_deploy = {
    "name": "Build and deploy app",
    "on": {
        "pull_request": {"branches": ["master"]},
        "push": {"branches": ["master"]},
        "workflow_dispatch": {},
    },
    "permissions": {},
    "env": {
        "_workflow_file_generator": "ci/gen-github-workflows.py",
        "image_name": "ghcr.io/${{ github.repository }}",
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
                        "tags": "${{ env.image_name }}:latest",
                    },
                },
                {
                    "name": "Log in to GitHub container registry",
                    "if": "github.even_name == 'push' || github.event_name == 'workflow_dispatch'",
                    "uses": "docker/login-action@v3",
                    "with": {
                        "password": "${{ github.token }}",
                        "registry": "ghcr.io",
                        "username": "${{ github.actor }}",
                    },
                },
                {
                    "name": "Push latest image to registry",
                    "if": "github.even_name == 'push' || github.event_name == 'workflow_dispatch'",
                    "uses": "docker/build-push-action@v6",
                    "with": {
                        "cache-from": "type=gha",
                        "push": True,
                        "tags": "${{ env.image_name }}:latest",
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
                {"name": "Check out the repository", "uses": "actions/checkout@v4"},
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

gen.gen(build_and_deploy, pathlib.Path(".github/workflows/build-and-deploy.yaml"))

ruff = {
    "name": "Ruff",
    "on": {"pull_request": {"branches": ["master"]}, "push": {"branches": ["master"]}},
    "permissions": {"contents": "read"},
    "env": {
        "_workflow_file_generator": "ci/gen-github-workflows.py",
    },
    "jobs": {
        "ruff": {
            "name": "Run ruff linting and formatting checks",
            "runs-on": "ubuntu-latest",
            "steps": [
                {"name": "Check out repository", "uses": "actions/checkout@v4"},
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

gen.gen(ruff, pathlib.Path(".github/workflows/ruff.yaml"))
