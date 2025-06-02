# backend/course/utils.py (如果创建此文件) 或 backend/course/views.py 顶部
import re
import json
from typing import Optional

import chardet  # 用于检测文件编码, pip install chardet

ALLOWED_EXTENSIONS = ['.txt', '.vue', '.py', '.html', '.js', '.sh', '.bash', '.json', '.c', '.cpp', '.java', '.md']
MAX_CONTENT_LENGTH = 15000  # 总字数限制


def extract_json_from_string(text_containing_json: str) -> Optional[dict]:
    """
    Extracts a JSON object from a string that might contain other text.
    It looks for the first '{' and the last '}' to define the JSON boundaries.
    This is a common heuristic but might fail for complex cases.
    """
    try:
        # 尝试找到第一个 '{' 和最后一个 '}' 来界定JSON对象
        # 更鲁棒的方法是寻找被 ```json ... ``` 包裹的部分
        match_triple_quotes = re.search(r"```json\s*(\{.*?\})\s*```", text_containing_json, re.DOTALL)
        if match_triple_quotes:
            json_str = match_triple_quotes.group(1)
        else:
            # 尝试直接从字符串中提取第一个 { 到最后一个 }
            first_brace = text_containing_json.find('{')
            last_brace = text_containing_json.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = text_containing_json[first_brace: last_brace + 1]
            else:  # 如果没有花括号，尝试方括号 (JSON数组)
                first_bracket = text_containing_json.find('[')
                last_bracket = text_containing_json.rfind(']')
                if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
                    json_str = text_containing_json[first_bracket: last_bracket + 1]
                else:
                    return None

        # 清理可能存在于JSON字符串前后的非JSON字符（例如，AI的额外解说）
        # 这是一个基本尝试，可能需要更复杂的清理
        json_str_cleaned = json_str.strip()
        parsed_json = json.loads(json_str_cleaned)
        return parsed_json
    except json.JSONDecodeError:
        # 如果严格的JSON解析失败，可以尝试更宽松的正则匹配，但风险较高
        # 例如，匹配包含 "score" 和 "comment" 的最小JSON对象
        # 这里简单返回None
        return None
    except Exception:
        return None


def read_uploaded_file_content(uploaded_file) -> Optional[str]:
    """Reads content from an InMemoryUploadedFile or TemporaryUploadedFile."""
    try:
        uploaded_file.seek(0)  # Ensure reading from the beginning
        raw_data = uploaded_file.read()
        # Detect encoding
        detected_encoding = chardet.detect(raw_data)['encoding']
        if detected_encoding:
            return raw_data.decode(detected_encoding, errors='replace')
        else:
            # Fallback if chardet fails (less likely for text files)
            return raw_data.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Error reading file {uploaded_file.name}: {e}")
        return None
