import re
from pathlib import Path

from utility.patterns import load_patterns_json, compile_regex_patterns
from utility.file_utils import validate_input

# ========== Config ==========

def load_config(patterns_config: Path, pattern_key: str) -> tuple[dict, re.Pattern]:
    if not validate_input(patterns_config):
        raise FileNotFoundError(patterns_config)

    patterns_json = load_patterns_json(patterns_config)

    if pattern_key not in patterns_json:
        raise ValueError(f"Invalid key: {pattern_key}")

    compiled = compile_regex_patterns(patterns_json[pattern_key])
    header_regex = compiled["base"]["header"]

    return compiled, header_regex