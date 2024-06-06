def read_key_value_pairs(file_path: str) -> dict:
    """
    指定されたファイルパスからキーと値のペアを読み取り、辞書として返します。

    Args:
        file_path (str): 読み込むファイルのパス

    Returns:
        dict: キーと値のペアを格納した辞書
    """
    key_value_pairs = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # 引用符で囲まれている場合は、引用符を取り除く
                if value.startswith('"') and value.endswith('"') or \
                   value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                key_value_pairs[key] = value
    return key_value_pairs