import dagger
import os
from dagger import dag, function, object_type
from decouple import config
from pathlib import Path
from textwrap import dedent

@object_type
class BuildDagger:
    @staticmethod
    def _get_base_python_container() -> dagger.Container:
        """Creates a base Python container with required dependencies"""
        return (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "python-decouple", "names"])
        )

    # Constants
    REGISTRY = config("REGISTRY", default="ghcr.io")
    ORGANIZATION = config("ORGANIZATION", default="pythoninthegrass")
    IMAGE = config("IMAGE", default="")
    PROFILE = config("PROFILE", default="dev")
    TARGETARCH = config("TARGETARCH", default="amd64")

    # Initialize environment variables
    os.environ["PROFILE"] = PROFILE
    os.environ["TARGETARCH"] = TARGETARCH

    @function
    async def build(self, dockerfile_path: str = "Dockerfile") -> str:
        """
        Builds and publishes a Docker image using the specified Dockerfile.

        Args:
            dockerfile_path: Path to the Dockerfile (default: "Dockerfile")

        Returns:
            str: The image reference of the published container
        """
        container = self._get_base_python_container()

        tag = await self._generate_tag(dockerfile_path, container)
        full_tag = f"{self.REGISTRY}/{self.ORGANIZATION}/{tag}"

        try:
            project_dir = str(Path(__file__).parent.parent.parent)
            ctx = dag.host().directory(project_dir)

            image = ctx.docker_build(dockerfile=f"./{dockerfile_path}")
            image_ref = await image.publish(full_tag)
            return image_ref
        except Exception as e:
            raise RuntimeError(f"Error building {dockerfile_path}: {str(e)}")

    async def _load_adjectives(self, container: dagger.Container) -> list:
        """Load adjectives from the adjectives.csv file"""
        project_dir = str(Path(__file__).parent.parent.parent)
        ctx = dag.host().directory(project_dir)

        result = await (
            container
            .with_mounted_directory("/src", ctx)
            .with_workdir("/src")
            .with_exec(["python", "-c", dedent("""
                import csv
                with open('adjectives.csv', 'r') as f:
                    print(','.join(adj.strip() for adj in f if adj.strip()))
            """)])
            .stdout()
        )
        return result.strip().split(',')

    async def _generate_docker_style_name(self, container: dagger.Container) -> str:
        """Generate a Docker-style name combining an adjective with a random name"""
        adjectives = await self._load_adjectives(container)
        result = await (
            container
            .with_exec(["python", "-c", dedent(f"""
                import random
                from names import get_full_name
                adjectives = {repr(adjectives)}
                adjective = random.choice(adjectives).lower()
                full_name = get_full_name().split()[-1].lower()
                print(f"{{adjective}}_{{full_name}}")
            """)])
            .stdout()
        )
        return result.strip()

    async def _generate_tag(self, dockerfile: str, container: dagger.Container) -> str:
        """Generate appropriate tag based on priority"""
        if '.' in dockerfile:
            return dockerfile.split('.', 1)[-1]
        elif self.IMAGE:
            return self.IMAGE
        else:
            return await self._generate_docker_style_name(container)
