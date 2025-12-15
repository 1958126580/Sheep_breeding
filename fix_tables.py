#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix table formatting in USER_MANUAL_ZH.md"""

import re

# Read the file with UTF-8 encoding
with open('docs/USER_MANUAL_ZH.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the table separators
# Replace "| 方法 |" with "| 方法   |" (add spaces to match column width)
content = re.sub(r'\| 方法 \| 路径', '| 方法   | 路径', content)

# Replace "| ---- |" with "| ------ |" (standardize separator width)
content = re.sub(r'\| ---- \|', '| ------ |', content)

# Write back with UTF-8 encoding
with open('docs/USER_MANUAL_ZH.md', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

print("Table formatting fixed successfully!")
