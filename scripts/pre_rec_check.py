# -*- coding: utf-8 -*-
"""录屏前环境一键自检：容器、端口、模型预热状态。"""
import subprocess, sys, urllib.request, json

ok = True

def check(name, cond, extra=""):
    global ok
    mark = "✅" if cond else "❌"
    if not cond:
        ok = False
    print(f"{mark} {name}{(' — ' + extra) if extra else ''}")

print("=== CleanDoc 录屏前自检 ===\n")

# 1. 容器
try:
    ps = subprocess.run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                        capture_output=True, text=True, timeout=15).stdout
    check("cleandoc 容器运行", "cleandoc" in ps and "Up" in ps.split("cleandoc")[1][:8] if "cleandoc" in ps else False)
    check("archrag-neo4j 容器运行", "archrag-neo4j" in ps and "Up" in ps.split("archrag-neo4j")[1][:8] if "archrag-neo4j" in ps else False)
except Exception as e:
    check("docker 可用", False, str(e))

# 2. 端口
try:
    code = urllib.request.urlopen("http://localhost:8502/_stcore/health", timeout=5).status
    check("8502 健康检查", code == 200, f"HTTP {code}")
except Exception as e:
    check("8502 健康检查", False, str(e))

# 3. 模型预热提示（首次生成 90s，录前先跑一次）
print("\n💡 提示：录屏前先在浏览器手动生成一次交底（约 90s，预热模型），")
print("   再刷新页面回到初始表单，开始录制。")

print("\n" + ("✅ 环境就绪，可以录屏" if ok else "⚠️ 有项未通过，先解决再录屏"))
sys.exit(0 if ok else 1)
