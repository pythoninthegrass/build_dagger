"""
Dagger build module for container image management.

This module provides functionality for building and publishing Docker images
using Dagger. It supports dynamic tag generation and multi-architecture builds.
"""

import dagger
from dagger import dag, function, object_type
from .builder import BuildDagger as BuildDagger

# Re-export the BuildDagger class to maintain the expected import path
__all__ = ['BuildDagger']
