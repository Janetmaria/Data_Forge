import re
from typing import Dict, Any, Optional


def _strip_articles(text: str) -> str:
    """Remove leading 'the', 'a', 'an' from a column name guess."""
    return re.sub(r'^(the|a|an)\s+', '', text.strip())


def parse_command(command: str) -> Optional[Dict[str, Any]]:
    """
    Parse a natural language command string into a pipeline step dict.

    Returns a dict with keys ``operation`` and ``params``, or ``None`` if
    the command is not recognised.
    """
    cmd = command.strip()
    c   = cmd.lower()   # lower-case alias used for all pattern matching

    # ── 1. Drop Duplicates ────────────────────────────────────────────────
    if re.search(r'\b(drop|remove|delete)\s+dup(licate)?s?\b', c):
        return {"operation": "drop_duplicates", "params": {"columns": []}}

    # ── 2. Drop Column ────────────────────────────────────────────────────
    m = re.search(r'\b(?:drop|delete|remove)\s+col(?:umn)?\s+(.+)', c)
    if m:
        col = _strip_articles(m.group(1))
        return {"operation": "drop_columns", "params": {"columns": [col]}}

    # ── 3. Rename Column ─────────────────────────────────────────────────
    # "rename [col] to [new_name]"  |  "rename column [col] to [new_name]"
    m = re.search(r'\brename\s+(?:col(?:umn)?\s+)?(.+?)\s+to\s+(.+)', c)
    if m:
        old_col = _strip_articles(m.group(1))
        new_col = _strip_articles(m.group(2))
        return {"operation": "rename_columns", "params": {"mapping": {old_col: new_col}}}

    # ── 4. Filter / Keep rows ─────────────────────────────────────────────
    # "filter rows where age > 30"  |  "keep rows where salary < 50000"
    m = re.search(r'\b(?:filter|keep)\s+rows?\s+(?:where|when|with)?\s+(.+)', c)
    if m:
        condition = m.group(1).strip()
        return {"operation": "filter_rows", "params": {"condition": condition}}

    # ── 5. KNN Impute ─────────────────────────────────────────────────────
    # "knn impute age"  |  "knn impute age with k=3"  |  "knn fill salary"
    m = re.search(r'\bknn\s+(?:impute|fill)\s+(.+?)(?:\s+(?:with\s+)?k\s*=?\s*(\d+))?$', c)
    if m:
        col = _strip_articles(m.group(1))
        k   = int(m.group(2)) if m.group(2) else 5
        return {"operation": "knn_impute", "params": {"columns": [col], "n_neighbors": k}}

    # ── 6. Missingness Indicator / Flag ───────────────────────────────────
    # "flag missing in age"  |  "add missingness indicator for price"
    # "missingness flag salary"
    m = re.search(
        r'\b(?:flag|add\s+(?:missingness\s+)?(?:indicator|flag)|missingness\s+(?:flag|indicator))\s+(?:(?:for|in|on)\s+)?(.+)',
        c)
    if m:
        col = _strip_articles(m.group(1))
        return {"operation": "add_missingness_indicator",
                "params": {"columns": [col], "drop_original": False}}

    # ── 7. Encode Categorical ─────────────────────────────────────────────
    # "one hot encode department"  |  "label encode status"
    # "frequency encode city"  |  "binary encode name"
    # "target encode price using label"
    encode_pattern = re.search(
        r'\b(one[\s_-]?hot|label|ordinal|frequency|freq|target|binary)\s+encod\w*\s+(.+?)(?:\s+using\s+(.+))?$',
        c)
    if encode_pattern:
        method_raw = encode_pattern.group(1).replace('-', '').replace(' ', '')
        col        = _strip_articles(encode_pattern.group(2))
        target     = _strip_articles(encode_pattern.group(3)) if encode_pattern.group(3) else None
        method_map = {
            'onehot': 'one_hot', 'label': 'ordinal', 'ordinal': 'ordinal',
            'frequency': 'frequency', 'freq': 'frequency',
            'target': 'target', 'binary': 'binary',
        }
        method = method_map.get(method_raw, 'one_hot')
        params: Dict[str, Any] = {"column": col, "method": method}
        if target:
            params["target_column"] = target
        return {"operation": "encode_categorical", "params": params}

    # ── 8. Extract Numeric (from messy strings) ───────────────────────────
    # "extract numeric from price"  |  "extract number from revenue"
    # "extract numbers from salary (drop invalid)"
    m = re.search(r'\bextract\s+num(?:eric|ber)s?\s+(?:from|in)\s+(.+?)(?:\s+(drop|null)\s+invalid)?$', c)
    if m:
        col        = _strip_articles(m.group(1))
        on_invalid = 'drop' if m.group(2) == 'drop' else 'null'
        return {"operation": "extract_numeric",
                "params": {"columns": [col], "on_invalid": on_invalid}}

    # ── 9. Convert Type ───────────────────────────────────────────────────
    # words → numeric  |  numeric → words
    m = re.search(r'\b(?:convert\s+)?(.+?)\s+(?:text|words?)\s+to\s+(?:numeric|numbers?)\b', c)
    if m:
        col = _strip_articles(m.group(1))
        return {"operation": "convert_type",
                "params": {"columns": [col], "type": "text_to_numeric"}}

    m = re.search(r'\b(?:convert\s+)?(.+?)\s+(?:numeric|numbers?)\s+to\s+(?:text|words?)\b', c)
    if m:
        col = _strip_articles(m.group(1))
        return {"operation": "convert_type",
                "params": {"columns": [col], "type": "numeric_to_text"}}

    m = re.search(r'\bconvert\s+(.+?)\s+to\s+(string|text|number|numeric|date|int|float)\b', c)
    if m:
        col    = _strip_articles(m.group(1))
        target = m.group(2)
        type_map = {"number": "numeric", "numeric": "numeric", "int": "numeric",
                    "float": "numeric", "date": "date", "string": "string", "text": "string"}
        return {"operation": "convert_type",
                "params": {"columns": [col], "type": type_map.get(target, "string")}}

    # ── 10. Round Numeric ─────────────────────────────────────────────────
    m = re.search(r'\bround\s+(.+?)\s+to\s+(\d+)\s+(?:decimal|d\.?p\.?|places?)\b', c)
    if m:
        col      = _strip_articles(m.group(1))
        decimals = int(m.group(2))
        return {"operation": "round_numeric", "params": {"columns": [col], "decimals": decimals}}

    # ── 11a. Drop Missing — global ─────────────────────────────────────────
    if re.search(r'\b(?:drop|remove)\s+(?:all\s+)?(?:missing|null|nan)(?:\s+rows?|\s+values?|\s+data)?$', c):
        return {"operation": "drop_missing", "params": {"columns": []}}

    # ── 11b. Drop Missing — column-specific ───────────────────────────────
    m = re.search(r'\b(?:drop|remove)\s+(?:missing|null|nan)(?:\s+values?)?\s+(?:from|in)\s+(.+)', c)
    if m:
        col = _strip_articles(m.group(1))
        return {"operation": "drop_missing", "params": {"columns": [col]}}

    # ── 12. Fill Missing ─────────────────────────────────────────────────
    m = re.search(r'\bfill\s+(?:missing|null|nan)(?:\s+values?)?\s+in\s+(.+?)\s+with\s+(mean|median|mode|.+)', c)
    if m:
        col = _strip_articles(m.group(1))
        val = m.group(2).strip()
        if val in ("mean", "median", "mode"):
            return {"operation": "fill_missing",
                    "params": {"columns": [col], "method": val, "value": None}}
        return {"operation": "fill_missing",
                "params": {"columns": [col], "method": "constant", "value": val}}

    # Custom fill shorthand: "fill age with 0"  |  "fill department with Unknown"
    m = re.search(r'\bfill\s+(.+?)\s+with\s+(.+)$', c)
    if m:
        col = _strip_articles(m.group(1))
        val = m.group(2).strip()
        if val in ("mean", "median", "mode"):
            return {"operation": "fill_missing",
                    "params": {"columns": [col], "method": val, "value": None}}
        return {"operation": "fill_missing",
                "params": {"columns": [col], "method": "constant", "value": val}}

    # ── 13. Text Case ────────────────────────────────────────────────────
    m = re.search(r'\b(uppercase|lowercase|titlecase|title\s+case|upper\s+case|lower\s+case)\s+(.+)', c)
    if m:
        raw  = m.group(1).replace(' ', '')
        col  = _strip_articles(m.group(2))
        case = 'upper' if raw.startswith('upper') else 'lower' if raw.startswith('lower') else 'title'
        return {"operation": "text_case", "params": {"columns": [col], "case": case}}

    # ── 14. Standard / Z-Score Scale ────────────────────────────────────
    m = re.search(r'\b(?:standard\s+scale|zscore|z-score|standardize|standardise)\s+(.+)', c)
    if m:
        col = _strip_articles(m.group(1))
        return {"operation": "standard_scale", "params": {"columns": [col]}}

    # ── 15. Min-Max Normalize ────────────────────────────────────────────
    m = re.search(r'\bscale\s+(.+?)(?:\s+between\s+(-?\d+(?:\.\d+)?)\s+and\s+(-?\d+(?:\.\d+)?))?$', c)
    if m:
        col     = _strip_articles(m.group(1))
        params  = {"columns": [col]}
        if m.group(2) and m.group(3):
            params["feature_min"] = float(m.group(2))
            params["feature_max"] = float(m.group(3))
        return {"operation": "normalize", "params": params}

    # ── 16. Outlier Removal (drop) ───────────────────────────────────────
    m = re.search(r'\b(?:remove|drop)\s+outliers?\s+(?:from|in)\s+(.+)', c)
    if m:
        col = _strip_articles(m.group(1))
        return {"operation": "remove_outliers_iqr",
                "params": {"columns": [col], "multiplier": 1.5}}

    # ── 17. Outlier Cap ──────────────────────────────────────────────────
    # "cap outliers in salary"  |  "cap outliers in age iqr 2.0"
    m = re.search(r'\bcap\s+outliers?\s+(?:in|for)\s+(.+?)(?:\s+(?:iqr|fold|multiplier)\s+(-?\d+(?:\.\d+)?))?$', c)
    if m:
        col  = _strip_articles(m.group(1))
        fold = float(m.group(2)) if m.group(2) else 1.5
        return {"operation": "handle_outliers",
                "params": {"columns": [col], "method": "iqr", "fold": fold, "strategy": "cap"}}

    # ── 18. Time-Series Fill (ffill / bfill) ─────────────────────────────
    m = re.search(r'\b(ffill|forward[\s-]fill|forward\s+fill)\s+(.+)', c)
    if m:
        col = _strip_articles(m.group(2))
        return {"operation": "time_series_fill", "params": {"columns": [col], "method": "ffill"}}

    m = re.search(r'\b(bfill|backward[\s-]fill|backward\s+fill|back[\s-]fill)\s+(.+)', c)
    if m:
        col = _strip_articles(m.group(2))
        return {"operation": "time_series_fill", "params": {"columns": [col], "method": "bfill"}}

    # ── 19. Date Extraction (legacy simple) ──────────────────────────────
    # "extract date join_date"  |  "parse date created_at"
    m = re.search(r'\b(?:extract|parse)\s+date(?:time)?\s+(.+)', c)
    if m:
        col = _strip_articles(m.group(1))
        return {"operation": "extract_datetime", "params": {"columns": [col]}}

    # ── 20. Extract Datetime Components (rich) ───────────────────────────
    # "extract year month day from join_date"
    # "extract year quarter from created_at"
    # "extract hour minute from timestamp"
    COMPONENTS = ['year', 'month', 'day', 'hour', 'minute', 'dayofweek', 'dayofyear',
                  'weekofyear', 'quarter', 'is_weekend', 'is_month_start', 'is_month_end']
    comp_pattern = '|'.join(re.escape(x) for x in COMPONENTS)
    m = re.search(
        rf'\bextract\s+((?:(?:{comp_pattern})[\s,]+)+)(?:from|in)\s+(.+)',
        c)
    if m:
        raw_comps = re.findall(comp_pattern, m.group(1))
        col = _strip_articles(m.group(2))
        if raw_comps and col:
            return {"operation": "extract_datetime_components",
                    "params": {"column": col, "components": raw_comps}}

    # Extract single component: "extract year from join_date"
    m = re.search(rf'\bextract\s+({comp_pattern})\s+(?:from|of|in)\s+(.+)', c)
    if m:
        comp = m.group(1)
        col  = _strip_articles(m.group(2))
        return {"operation": "extract_datetime_components",
                "params": {"column": col, "components": [comp]}}

    # ── 21. Lag Features ──────────────────────────────────────────────────
    # "lag features for price with lags 1 2 3"
    # "create lag 3 for sales"  |  "add lag 1 2 to revenue"
    m = re.search(r'\b(?:lag\s+features?\s+(?:for|on|in)|(?:create|add)\s+lag)\s+(.+?)\s+(?:with\s+lags?\s+|lags?\s+)?([\d\s,]+)', c)
    if m:
        col  = _strip_articles(m.group(1))
        lags = [int(x) for x in re.findall(r'\d+', m.group(2))]
        if lags:
            return {"operation": "create_lag_features",
                    "params": {"column": col, "lags": lags}}

    # Alternative: "lag 1 2 3 for price"
    m = re.search(r'\blag\s+([\d\s,]+)\s+(?:for|of)\s+(.+)', c)
    if m:
        lags = [int(x) for x in re.findall(r'\d+', m.group(1))]
        col  = _strip_articles(m.group(2))
        if lags:
            return {"operation": "create_lag_features",
                    "params": {"column": col, "lags": lags}}

    # ── 22. Rolling Features ─────────────────────────────────────────────
    # "rolling mean of price window 7"
    # "rolling mean std of revenue window 3 7"
    # "create rolling features for sales windows 3 7"
    STATS = ['mean', 'std', 'min', 'max', 'median']
    stat_pattern = '|'.join(STATS)
    m = re.search(
        rf'\brolling\s+((?:(?:{stat_pattern})[\s,]*)+)\s+(?:of|for)\s+(.+?)\s+window\s+([\d\s,]+)',
        c)
    if m:
        raw_stats = re.findall(stat_pattern, m.group(1))
        col       = _strip_articles(m.group(2))
        windows   = [int(x) for x in re.findall(r'\d+', m.group(3))]
        if col and windows:
            return {"operation": "create_rolling_features",
                    "params": {"column": col, "windows": windows,
                               "stats": raw_stats or ["mean", "std"]}}

    # "create rolling features for price windows 3 7"
    m = re.search(r'\b(?:create|add)\s+rolling\s+features?\s+(?:for|on|in)\s+(.+?)\s+windows?\s+([\d\s,]+)', c)
    if m:
        col     = _strip_articles(m.group(1))
        windows = [int(x) for x in re.findall(r'\d+', m.group(2))]
        if col and windows:
            return {"operation": "create_rolling_features",
                    "params": {"column": col, "windows": windows, "stats": ["mean", "std"]}}

    # ── 23. Bin Column ────────────────────────────────────────────────────
    # "bin age into 5"  |  "bin salary 4 equal width"
    # "bin age 5 equal frequency"  |  "quantile bin age 5"
    m = re.search(r'\b(?:quantile|equal[\s_-]?freq(?:uency)?)\s+bin\s+(.+?)\s+(\d+)', c)
    if m:
        col    = _strip_articles(m.group(1))
        n_bins = int(m.group(2))
        return {"operation": "bin_column",
                "params": {"column": col, "strategy": "equal_frequency", "n_bins": n_bins}}

    m = re.search(r'\bbin\s+(.+?)\s+(?:into\s+)?(\d+)(?:\s+(?:equal[\s_-]?freq(?:uency)?|quantile))?$', c)
    if m:
        col      = _strip_articles(m.group(1))
        n_bins   = int(m.group(2))
        strategy_hint = m.group(0)
        strategy = 'equal_frequency' if re.search(r'freq|quantile', strategy_hint) else 'equal_width'
        return {"operation": "bin_column",
                "params": {"column": col, "strategy": strategy, "n_bins": n_bins}}

    # ── 24. Handle Imbalance (SMOTE / undersample) ───────────────────────
    # "smote target_col"  |  "balance classes using target_col"
    # "oversample target_col"  |  "undersample target_col"
    # "handle imbalance on target_col"
    m = re.search(
        r'\b(?:smote|balance\s+classes?\s+(?:using|on|for)|handle\s+imbalance\s+(?:on|for)|oversample|undersample)\s+(.+)',
        c)
    if m:
        target = _strip_articles(m.group(1))
        strategy = 'undersample' if 'undersample' in c else 'smote'
        return {"operation": "handle_imbalance",
                "params": {"target_column": target, "strategy": strategy, "k_neighbors": 5}}

    # ── 25. Format Validation ─────────────────────────────────────────────
    m = re.search(r'\bvalidate\s+(email|phone|url|ip(?:\s+address)?|credit[\s_-]?card|aadhaar)\s+(?:format\s+)?(?:in|for|on)?\s*(.+)', c)
    if m:
        fmt_raw = m.group(1).lower().replace(' ', '_').replace('-', '_')
        col     = _strip_articles(m.group(2))
        fmt_map = {'ip': 'ip_address', 'ip_address': 'ip_address',
                   'credit_card': 'credit_card', 'creditcard': 'credit_card'}
        fmt_type = fmt_map.get(fmt_raw, fmt_raw)
        return {"operation": "validate_format",
                "params": {"columns": [col], "format_type": fmt_type, "action": "set_null"}}

    # ── Not recognised ────────────────────────────────────────────────────
    return None
