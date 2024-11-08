#!/usr/bin/env python

import anyio
import dagger
import os
import random
import string
import sys
from decouple import config
from names import get_full_name
from pathlib import Path
from typing import Tuple, List

REGISTRY = config("REGISTRY", default="ghcr.io")
ORGANIZATION = config("ORGANIZATION", default="pythoninthegrass")
IMAGE = config("IMAGE", default="")
PROFILE = config("PROFILE", default="dev")
TARGETARCH = config("TARGETARCH", default="amd64")

# add profile and target arch to env vars
os.environ["PROFILE"] = PROFILE
os.environ["TARGETARCH"] = TARGETARCH

# List of Dockerfile paths
dockerfiles = [
    "Dockerfile"
]


def load_adjectives() -> list:
    """
    Load adjectives from a local CSV file.
    Returns a list of adjectives.
    """
    adjectives_path = Path(__file__).parent / "adjectives.csv"
    return [adj.strip() for adj in adjectives_path.read_text().splitlines() if adj.strip()]


def generate_docker_style_name() -> str:
    """
    Generate a Docker-style name combining an adjective with a random name.
    Returns a string like 'eloquent_einstein' or 'clever_curie'
    """
    adjectives = load_adjectives()
    adjective = random.choice(adjectives).lower()
    full_name = get_full_name().split()[-1].lower()
    return f"{adjective}_{full_name}"


def generate_tag(dockerfile: str) -> Tuple[str, str]:
    """
    Generate appropriate tag based on priority:
    1. Dockerfile suffix if present
    2. IMAGE env var if set
    3. Docker-style random name

    Returns tuple of (dockerfile_path, tag)
    """
    dockerfile_path = dockerfile

    # Generate tag based on priority
    if '.' in dockerfile:
        tag = dockerfile.split('.', 1)[-1]
    elif IMAGE:
        tag = IMAGE
    else:
        tag = generate_docker_style_name()

    return (dockerfile_path, tag)


def get_dockerfile_tags() -> List[Tuple[str, str]]:
    """
    Process all dockerfiles and return list of (dockerfile_path, tag) tuples
    """
    return [generate_tag(dockerfile) for dockerfile in dockerfiles]


async def build():
    async with dagger.Connection(dagger.Config(log_output=sys.stdout)) as client:
        project_dir = str(Path(__file__).parent)
        ctx = client.host().directory(project_dir)

        dockerfile_tags = get_dockerfile_tags()

        for dockerfile_path, tag_suffix in dockerfile_tags:
            tag = f"{REGISTRY}/{ORGANIZATION}/{tag_suffix}"

            try:
                image = ctx.docker_build(dockerfile=f"./{dockerfile_path}")
                image_ref = await image.publish(tag)
                print(f"Built image and pushed to: {image_ref}")
            except dagger.QueryError as e:
                print(f"Error building {dockerfile_path}: {str(e)}")
                continue


anyio.run(build)
