#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量重命名系统名称
从 "新星肉羊育种系统 / NovaBreed Sheep System"
到 "新星肉羊育种系统 / NovaBreed Sheep System"
"""

import os
import re
from pathlib import Path

# 定义替换规则
REPLACEMENTS = [
    ("新星肉羊育种系统", "新星肉羊育种系统"),
    ("NovaBreed Sheep System", "NovaBreed Sheep System"),
    ("NovaBreed Sheep System", "NovaBreed Sheep System"),
]

# 需要处理的文件扩展名
EXTENSIONS = ['.md', '.py', '.jl', '.sql', '.yml', '.yaml', '.tsx', '.ts', '.json']

# 排除的目录
EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.gemini'}

def should_process_file(file_path):
    """判断文件是否需要处理"""
    # 检查扩展名
    if file_path.suffix not in EXTENSIONS:
        return False
    
    # 检查是否在排除目录中
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in file_path.parts:
            return False
    
    return True

def replace_in_file(file_path):
    """在文件中执行替换"""
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 执行替换
        original_content = content
        for old_text, new_text in REPLACEMENTS:
            content = content.replace(old_text, new_text)
        
        # 如果有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """主函数"""
    base_dir = Path('.')
    modified_files = []
    
    print("开始批量重命名...")
    print(f"工作目录: {base_dir.absolute()}")
    print()
    
    # 遍历所有文件
    for file_path in base_dir.rglob('*'):
        if file_path.is_file() and should_process_file(file_path):
            if replace_in_file(file_path):
                modified_files.append(file_path)
                print(f"✓ {file_path}")
    
    print()
    print(f"完成！共修改 {len(modified_files)} 个文件")
    
    if modified_files:
        print("\n修改的文件列表:")
        for file_path in modified_files:
            print(f"  - {file_path}")

if __name__ == "__main__":
    main()
