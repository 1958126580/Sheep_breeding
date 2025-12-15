# ============================================================================
# 国际顶级肉羊育种系统 - 综合测试运行器
# International Top-tier Sheep Breeding System - Comprehensive Test Runner
#
# 文件: run_all_tests.py
# 用途: 一键运行所有测试并生成覆盖率报告
# 使用方法: python run_all_tests.py
# ============================================================================

"""
综合测试运行器

这个脚本用于一键运行所有Python测试，包括:
1. 模型层测试 (test_models.py)
2. 服务层测试 (test_services.py) 
3. API层测试 (test_api.py)

运行方式:
    python run_all_tests.py          # 运行所有测试
    python run_all_tests.py --cov    # 运行并生成覆盖率报告
    python run_all_tests.py --quick  # 快速测试模式
"""

import subprocess
import sys
import os
from datetime import datetime


def print_header(message: str):
    """打印格式化的标题"""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)


def run_tests(with_coverage: bool = False, quick_mode: bool = False):
    """
    运行测试套件
    
    参数:
        with_coverage: 是否生成覆盖率报告
        quick_mode: 是否使用快速模式(跳过慢测试)
    
    返回:
        int: 测试退出码 (0=成功)
    """
    # 切换到正确的目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print_header(f"开始测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 构建pytest命令
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    
    if with_coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
        print("📊 启用覆盖率报告")
    
    if quick_mode:
        cmd.extend(["-x", "--tb=line"])  # 遇到第一个失败就停止
        print("⚡ 快速模式已启用")
    else:
        cmd.extend(["--tb=short"])
    
    # 测试分类
    test_categories = [
        ("模型层测试", "test_models.py"),
        ("服务层测试", "test_services.py"),
        ("API层测试", "test_api.py"),
    ]
    
    print("\n📋 将要运行的测试:")
    for name, file in test_categories:
        print(f"   ✓ {name} ({file})")
    
    print("\n" + "-" * 70)
    
    # 运行测试
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    
    # 打印结果摘要
    print("\n" + "-" * 70)
    if result.returncode == 0:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败，请检查上面的输出")
    
    if with_coverage:
        print("\n📊 覆盖率报告已生成: htmlcov/index.html")
    
    return result.returncode


def main():
    """主函数"""
    with_cov = "--cov" in sys.argv or "-c" in sys.argv
    quick = "--quick" in sys.argv or "-q" in sys.argv
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return 0
    
    return run_tests(with_coverage=with_cov, quick_mode=quick)


if __name__ == "__main__":
    sys.exit(main())
