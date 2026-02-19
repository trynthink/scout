"""Shared helper functions for JSON Schema validation tests.

This module provides reusable utility functions for validating JSON files
against JSON Schema definitions. It includes functions for resolving schema
references, extracting descriptions, patterns, and enum values from complex
schema structures.

These helpers are used by:
- ecm_schema_test.py: ECM definition validation
- mseg_cpl_res_coms_cz_schema_test.py: Supporting data validation
"""


def resolve_ref(schema, validator, depth=0, max_depth=10):
    """Resolve a $ref to its actual schema definition.

    Recursively follows $ref pointers in JSON Schema to find the actual
    schema definition. Prevents infinite loops with depth limiting.

    Args:
        schema: Schema (or sub-schema) potentially containing $ref
        validator: JSON schema validator instance with schema definitions
        depth: Current recursion depth (default: 0)
        max_depth: Maximum recursion depth to prevent infinite loops
            (default: 10)

    Returns:
        Resolved schema definition (dict)

    Example:
        >>> schema = {"$ref": "#/definitions/myType"}
        >>> validator = Draft202012Validator(full_schema)
        >>> resolved = resolve_ref(schema, validator)
        >>> # Returns the actual definition of 'myType'
    """
    if depth > max_depth or "$ref" not in schema:
        return schema
    ref_path = schema["$ref"]
    if ref_path.startswith("#/definitions/"):
        def_name = ref_path.split("/")[-1]
        resolved = validator.schema.get("definitions", {}).get(def_name, {})
        return resolve_ref(resolved, validator, depth + 1)
    return schema


def extract_enums(schema, validator, depth=0, max_depth=10):
    """Recursively extract enum values from schema and references.

    Handles complex schema structures including:
    - Direct enum arrays
    - anyOf/oneOf with nested schemas
    - $ref definitions
    - Array items with enums

    Args:
        schema: Schema (or sub-schema) to extract enums from
        validator: JSON schema validator instance
        depth: Current recursion depth (default: 0)
        max_depth: Maximum recursion depth to prevent infinite loops
            (default: 10)

    Returns:
        List of all enum values found (may contain duplicates)

    Example:
        >>> schema = {"anyOf": [{"enum": ["A", "B"]}, {"enum": ["C"]}]}
        >>> extract_enums(schema, validator)
        ["A", "B", "C"]
    """
    if depth > max_depth:
        return []

    enums = []

    # Direct enum
    if "enum" in schema:
        enums.extend(schema["enum"])
        return enums

    # Handle anyOf (standard) and oneOf (legacy support)
    for key in ["anyOf", "oneOf"]:
        if key in schema:
            for sub_schema in schema[key]:
                enums.extend(
                    extract_enums(sub_schema, validator, depth + 1)
                )

    # Handle $ref
    if "$ref" in schema:
        resolved = resolve_ref(schema, validator, depth)
        if resolved != schema:
            enums.extend(extract_enums(resolved, validator, depth + 1))

    # Handle array items
    if "items" in schema:
        enums.extend(extract_enums(schema["items"], validator, depth + 1))

    return enums


def extract_descriptions(schema, validator, depth=0, max_depth=10):
    """Extract descriptions from schema and its references.

    Traverses complex schema structures to find description fields,
    including nested anyOf/oneOf and $ref definitions. Useful for
    providing context in error messages.

    Args:
        schema: Schema to extract descriptions from
        validator: JSON schema validator instance
        depth: Current recursion depth (default: 0)
        max_depth: Maximum recursion depth to prevent infinite loops
            (default: 10)

    Returns:
        List of description strings found in schema

    Example:
        >>> schema = {
        ...     "description": "Main",
        ...     "anyOf": [{"description": "Sub"}]
        ... }
        >>> extract_descriptions(schema, validator)
        ["Main", "Sub"]
    """
    if depth > max_depth:
        return []
    descs = []
    if "description" in schema:
        descs.append(schema["description"])

    for key in ["anyOf", "oneOf"]:
        if key in schema:
            for sub_schema in schema[key]:
                resolved = resolve_ref(sub_schema, validator, depth)
                descs.extend(
                    extract_descriptions(resolved, validator, depth + 1)
                )

    if "$ref" in schema and "description" not in schema:
        resolved = resolve_ref(schema, validator, depth)
        if resolved != schema:
            descs.extend(
                extract_descriptions(resolved, validator, depth + 1)
            )

    return descs


def extract_patterns(schema, validator, depth=0, max_depth=10):
    """Extract pattern constraints from schema and its references.

    Finds regex patterns and patternProperties keys used for string
    validation, including patterns in nested anyOf/oneOf structures
    and $ref definitions.

    Args:
        schema: Schema to extract patterns from
        validator: JSON schema validator instance
        depth: Current recursion depth (default: 0)
        max_depth: Maximum recursion depth to prevent infinite loops
            (default: 10)

    Returns:
        List of pattern strings (regex or patternProperties keys)

    Example:
        >>> schema = {"pattern": "^[0-9]+$"}
        >>> extract_patterns(schema, validator)
        ["^[0-9]+$"]
    """
    if depth > max_depth:
        return []
    patterns = []

    if "pattern" in schema:
        patterns.append(schema["pattern"])
    if "patternProperties" in schema:
        patterns.extend(schema["patternProperties"].keys())

    for key in ["anyOf", "oneOf"]:
        if key in schema:
            for sub_schema in schema[key]:
                resolved = resolve_ref(sub_schema, validator, depth)
                patterns.extend(
                    extract_patterns(resolved, validator, depth + 1)
                )

    if "$ref" in schema and "pattern" not in schema:
        resolved = resolve_ref(schema, validator, depth)
        if resolved != schema:
            patterns.extend(
                extract_patterns(resolved, validator, depth + 1)
            )

    return patterns
