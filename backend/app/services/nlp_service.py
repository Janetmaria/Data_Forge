import re
from typing import Dict, Any

def parse_command(command: str) -> Dict[str, Any]:
    """
    Parses a natural language command into a pipeline step.
    Supported commands:
    - "convert [col] to string/text/number/numeric"
    - "round [col] to [X] decimal places"
    - "drop missing/null from [col]"
    - "fill missing in [col] with [value/mean/mode]"
    - "drop duplicates"
    - "delete/drop column [col]"
    - "uppercase/lowercase [col]"
    """
    cmd = command.lower().strip()
    
    # 1. Drop Duplicates
    if "drop duplicates" in cmd or "remove duplicates" in cmd:
        return {"operation": "drop_duplicates", "params": {"columns": []}}

    # 2. Drop Column
    drop_col_match = re.search(r"(?:drop|delete|remove) column (.+)", cmd)
    if drop_col_match:
        col = drop_col_match.group(1).strip()
        return {"operation": "drop_columns", "params": {"columns": [col]}}

    # 3. Convert Type
    convert_match = re.search(r"convert (.+) to (string|text|number|numeric|date|int|float)", cmd)
    if convert_match:
        col = convert_match.group(1).strip()
        target = convert_match.group(2).strip()
        
        op_type = "string"
        if target in ["number", "numeric", "int", "float"]:
            op_type = "numeric"
        elif target == "date":
            op_type = "date"
            
        return {"operation": "convert_type", "params": {"columns": [col], "type": op_type}}

    # 4. Round Numeric
    round_match = re.search(r"round (.+) to (\d+) (?:decimal|places)", cmd)
    if round_match:
        col = round_match.group(1).strip()
        decimals = int(round_match.group(2))
        return {"operation": "round_numeric", "params": {"columns": [col], "decimals": decimals}}

    # 5. Drop Missing — global (no specific column)
    if re.search(r"(?:drop|remove) (?:all )?(?:missing|null|nan)(?: rows?| values?| data)?$", cmd):
        return {"operation": "drop_missing", "params": {"columns": []}}

    # 5b. Drop Missing — column-specific
    drop_missing_match = re.search(r"(?:drop|remove) (?:missing|null|nan)(?: values?)? (?:from|in) (.+)", cmd)
    if drop_missing_match:
        col = drop_missing_match.group(1).strip()
        return {"operation": "drop_missing", "params": {"columns": [col]}}

    # 6. Fill Missing
    fill_match = re.search(r"fill (?:missing|null|nan)(?: values?)? in (.+) with (mean|median|mode|.+)", cmd)
    if fill_match:
        col = fill_match.group(1).strip()
        val = fill_match.group(2).strip()
        
        method = "constant"
        value = val
        
        if val in ["mean", "median", "mode"]:
            method = val
            value = None
        
        return {"operation": "fill_missing", "params": {"columns": [col], "method": method, "value": value}}

    # 7. Text Case
    case_match = re.search(r"(uppercase|lowercase|titlecase) (.+)", cmd)
    if case_match:
        case_type = case_match.group(1).strip()
        col = case_match.group(2).strip()
        if case_type == "titlecase": case_type = "title"
        if case_type == "uppercase": case_type = "upper"
        if case_type == "lowercase": case_type = "lower"
        
        return {"operation": "text_case", "params": {"columns": [col], "case": case_type}}

    # 8. Standard Scaler — must be checked BEFORE min-max scale to avoid being swallowed
    if cmd.startswith("standard scale ") or cmd.startswith("zscore "):
        col = cmd.replace("standard scale ", "").replace("zscore ", "").strip()
        return {"operation": "standard_scale", "params": {"columns": [col]}}

    # 9. Min-Max Scaling
    scale_match = re.search(r"scale (.+?)(?: between (-?\d+(?:\.\d+)?) and (-?\d+(?:\.\d+)?))?$", cmd)
    if scale_match:
        col = scale_match.group(1).strip()
        min_val = scale_match.group(2)
        max_val = scale_match.group(3)
        
        params = {"columns": [col]}
        if min_val is not None and max_val is not None:
            params["feature_min"] = float(min_val)
            params["feature_max"] = float(max_val)
            
        return {"operation": "normalize", "params": params}

    # Custom Fills ("fill age with 0")
    custom_fill_match = re.search(r"fill (.+?) with (.+)$", cmd)
    if custom_fill_match:
        col = custom_fill_match.group(1).strip()
        val = custom_fill_match.group(2).strip()
        return {"operation": "fill_missing", "params": {"columns": [col], "method": "constant", "value": val}}

    # Outliers
    if re.search(r"(remove|drop) outliers (from|in) ", cmd):
        col = re.sub(r"^(remove|drop) outliers (from|in) ", "", cmd).strip()
        return {"operation": "remove_outliers_iqr", "params": {"columns": [col], "multiplier": 1.5}}

    # Date Extraction
    if cmd.startswith("extract date ") or cmd.startswith("parse date "):
        col = cmd.replace("extract date ", "").replace("parse date ", "").strip()
        return {"operation": "extract_datetime", "params": {"columns": [col]}}

    # Format Checking (Email/Phone/IP/URL/Credit Card/Aadhaar)
    format_match = re.search(r"validate (email|phone|ip|url|credit card|aadhaar) (format )?(in |for )?(.+)$", cmd, re.IGNORECASE)
    if format_match:
        fmt_str = format_match.group(1).lower()
        if fmt_str == "ip": 
            fmt_type = "ip_address"
        elif fmt_str == "credit card":
            fmt_type = "credit_card"
        else:
            fmt_type = fmt_str # email, phone, url, aadhaar directly map
            
        col = format_match.group(4).strip()
        return {"operation": "validate_format", "params": {"columns": [col], "format_type": fmt_type, "action": "set_null"}}

    return None
