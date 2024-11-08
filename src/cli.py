#!/usr/bin/env python

import anyio
from .builder import BuildDagger


async def main():
    """Entrypoint for building Docker images"""
    builder = BuildDagger()
    image_ref = await builder.build()
    print(f"Built image and pushed to: {image_ref}")


if __name__ == "__main__":
    anyio.run(main)
