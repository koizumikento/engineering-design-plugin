#!/bin/bash
#
# Engineering Design Plugin - Code Validation Hook
# Validates Python scripts before writing
#

# Read input from stdin (JSON format)
read -r INPUT

# Extract file path from tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty')

# Only validate Python files
if [[ "$FILE_PATH" != *.py ]]; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Create temporary file for validation
TEMP_FILE=$(mktemp /tmp/validate_XXXXXX.py)
echo "$CONTENT" > "$TEMP_FILE"

# 1. Python syntax check
SYNTAX_ERROR=$(python3 -m py_compile "$TEMP_FILE" 2>&1)
if [ $? -ne 0 ]; then
    rm -f "$TEMP_FILE"
    ERROR_MSG=$(echo "$SYNTAX_ERROR" | head -5 | tr '\n' ' ')
    echo "{\"decision\": \"block\", \"reason\": \"Python構文エラー: $ERROR_MSG\"}"
    exit 0
fi

# 2. Security check - dangerous imports
DANGEROUS_IMPORTS=$(grep -E "^import (os|subprocess|shutil|sys)|^from (os|subprocess|shutil|sys) import" "$TEMP_FILE")
if [ -n "$DANGEROUS_IMPORTS" ]; then
    rm -f "$TEMP_FILE"
    echo '{"decision": "ask", "reason": "システム操作を含むインポートが検出されました。このコードを実行してもよいですか？"}'
    exit 0
fi

# 3. Check for eval/exec (potential security risk)
EVAL_EXEC=$(grep -E "eval\(|exec\(" "$TEMP_FILE")
if [ -n "$EVAL_EXEC" ]; then
    rm -f "$TEMP_FILE"
    echo '{"decision": "ask", "reason": "eval()またはexec()が検出されました。このコードを実行してもよいですか？"}'
    exit 0
fi

# 4. CadQuery specific checks
if grep -q "import cadquery\|from cadquery" "$TEMP_FILE"; then
    # Check for isValid() assertion
    if ! grep -q "isValid()" "$TEMP_FILE"; then
        rm -f "$TEMP_FILE"
        echo '{"decision": "ask", "reason": "CadQueryスクリプトにisValid()チェックがありません。形状検証なしで続行しますか？"}'
        exit 0
    fi
fi

# 5. SKiDL specific checks
if grep -q "from skidl import\|import skidl" "$TEMP_FILE"; then
    # Check for ERC() call
    if ! grep -q "ERC()" "$TEMP_FILE"; then
        rm -f "$TEMP_FILE"
        echo '{"decision": "ask", "reason": "SKiDLスクリプトにERC()チェックがありません。電気的ルールチェックなしで続行しますか？"}'
        exit 0
    fi
fi

# Cleanup
rm -f "$TEMP_FILE"

# All checks passed
echo '{"decision": "allow"}'
exit 0
