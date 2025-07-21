#!/usr/bin/env python
"""
Generate OpenAPI schema from FastAPI application
"""
import json
import sys
import os

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


def generate_openapi_schema():
    """Generate OpenAPI schema and save to file"""
    schema = app.openapi()

    # Save to file
    output_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "openapi.json"
    )
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"OpenAPI schema generated at: {output_path}")
    return schema


if __name__ == "__main__":
    generate_openapi_schema()
