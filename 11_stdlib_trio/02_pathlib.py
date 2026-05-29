r"""
标准库 02：pathlib
─────────────────────────────────────────
内容：
1. Path 对象 ── 替代 os.path 的现代 API
2. 路径拼接 / 解析 / 规范化
3. 文件查询：exists / is_file / is_dir / stat
4. 遍历目录：iterdir / glob / rglob
5. 文件读写：read_text / write_text / read_bytes
6. 创建 / 移动 / 删除
7. 跨平台细节
"""

from pathlib import Path
import tempfile
import shutil


# ══════════════════════════════════════════════════════
# 1. Path 对象 ── 不再拼字符串
# ══════════════════════════════════════════════════════
# 旧：os.path.join("a", "b", "c.txt")
# 新：Path("a") / "b" / "c.txt"

p = Path("data") / "users" / "report.csv"
print("── Path 对象 ──")
print(p)                      # data/users/report.csv（Linux）或反斜杠（Windows）
print(type(p))                # <class 'pathlib.WindowsPath'> 或 PosixPath


# 几个常用入口
print(Path.cwd())             # 当前工作目录
print(Path.home())            # 用户主目录
print(Path(__file__))         # 当前文件本身的路径


# ══════════════════════════════════════════════════════
# 2. 路径解析：把一个路径拆成各部分
# ══════════════════════════════════════════════════════

p = Path("/var/log/app/error.log")

print("\n── 路径解析 ──")
print(p.name)        # 'error.log'      文件名（含扩展名）
print(p.stem)        # 'error'          文件名（不含扩展名）
print(p.suffix)      # '.log'           扩展名
print(p.parent)      # /var/log/app     上级目录
print(p.parents[0])  # /var/log/app
print(p.parents[1])  # /var/log
print(p.parents[2])  # /var
print(list(p.parts)) # ['/', 'var', 'log', 'app', 'error.log']  ← 各段


# 修改路径的某一部分
print(p.with_name("warning.log"))     # /var/log/app/warning.log
print(p.with_suffix(".txt"))           # /var/log/app/error.txt
print(p.with_stem("debug"))            # /var/log/app/debug.log


# 多个 suffix
p2 = Path("archive.tar.gz")
print(p2.suffixes)        # ['.tar', '.gz']
print(p2.suffix)          # '.gz'   只看最后一个


# ══════════════════════════════════════════════════════
# 3. 检查路径状态
# ══════════════════════════════════════════════════════

# 创建一个临时目录做演示
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)

    # 写一些文件
    (base / "a.txt").write_text("hello")
    (base / "b.log").write_text("log")
    (base / "subdir").mkdir()
    (base / "subdir" / "c.txt").write_text("nested")

    print("\n── 状态检查 ──")
    p = base / "a.txt"
    print(p.exists())          # True
    print(p.is_file())         # True
    print(p.is_dir())          # False
    print(p.stat().st_size)    # 5  (字节数)

    # 不存在的路径
    fake = base / "nope.txt"
    print(fake.exists())       # False


    # ══════════════════════════════════════════════════════
    # 4. 遍历目录
    # ══════════════════════════════════════════════════════

    print("\n── iterdir（直接子项）──")
    for item in base.iterdir():
        print(f"  {item.name}")


    print("\n── glob（当前层匹配）──")
    for f in base.glob("*.txt"):       # 只匹配当前目录
        print(f"  {f}")


    print("\n── rglob（递归匹配）──")
    for f in base.rglob("*.txt"):      # 递归所有层级
        print(f"  {f}")


    # 复杂模式
    print("\n── 复杂 glob 模式 ──")
    for f in base.glob("**/*.txt"):    # ** = 任意层目录
        print(f"  {f}")


    # ══════════════════════════════════════════════════════
    # 5. 文件读写：一行搞定
    # ══════════════════════════════════════════════════════

    p = base / "demo.txt"

    # 写文本
    p.write_text("Hello\nWorld\n", encoding="utf-8")

    # 读文本
    content = p.read_text(encoding="utf-8")
    print("\n── read_text ──")
    print(repr(content))

    # 写二进制
    bin_path = base / "demo.bin"
    bin_path.write_bytes(b"\x00\x01\x02")
    print(bin_path.read_bytes())


    # 大文件还是要用 open，按行/按块读
    print("\n── 大文件按行读 ──")
    with p.open(encoding="utf-8") as f:
        for line in f:
            print(f"  {line.rstrip()}")


    # ══════════════════════════════════════════════════════
    # 6. 创建目录
    # ══════════════════════════════════════════════════════

    new_dir = base / "level1" / "level2" / "level3"

    # parents=True 自动创建中间层
    # exist_ok=True 已存在不报错
    new_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n── mkdir ──")
    print(f"  {new_dir.exists()}")


    # ══════════════════════════════════════════════════════
    # 7. 重命名 / 移动 / 删除
    # ══════════════════════════════════════════════════════

    src = base / "demo.txt"
    dst = base / "renamed.txt"

    src.rename(dst)              # 重命名（src → dst）
    print(f"\n── rename ──")
    print(f"  存在: {dst.exists()}")
    print(f"  原文件: {src.exists()}")

    # 删除文件
    dst.unlink()                 # 删除文件
    print(f"  删除后: {dst.exists()}")

    # 删除空目录
    new_dir.rmdir()
    print(f"  目录删除: {not new_dir.exists()}")

    # 删除非空目录用 shutil（pathlib 不直接支持）
    shutil.rmtree(base / "subdir")


# 临时目录退出 with 后自动删除


# ══════════════════════════════════════════════════════
# 8. 路径转字符串
# ══════════════════════════════════════════════════════

p = Path("data/file.txt")
print("\n── 转字符串 ──")
print(str(p))          # 平台原生格式（Win 用反斜杠）
print(p.as_posix())    # 强制斜杠（跨平台一致）
print(p.resolve().as_uri())   # file:// URI（必须是绝对路径）


# ══════════════════════════════════════════════════════
# 9. 跨平台细节
# ══════════════════════════════════════════════════════
# 几个易错点：

# (a) 不要硬编码分隔符
# 错：path = "a" + "/" + "b"
# 对：path = Path("a") / "b"

# (b) 大小写：Linux/Mac 区分，Windows 不区分
# 写跨平台代码时，统一用小写更安全

# (c) 比较路径时先 resolve
p1 = Path("./demo.txt")
p2 = Path("demo.txt")
print(p1 == p2)              # False（字符串不一样）
# print(p1.resolve() == p2.resolve())  # True（解析成绝对路径再比较）


# ══════════════════════════════════════════════════════
# 10. 实战：递归统计目录大小
# ══════════════════════════════════════════════════════

def dir_size(path: Path) -> int:
    """返回目录下所有文件的总字节数"""
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


# 演示
with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    (base / "a.txt").write_text("x" * 100)
    (base / "b.txt").write_text("y" * 200)
    sub = base / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("z" * 300)

    print(f"\n── 递归统计 ──")
    print(f"  总大小: {dir_size(base)} 字节")    # 600


# ══════════════════════════════════════════════════════
# 11. 速查
# ══════════════════════════════════════════════════════
#
# 构造 / 拼接：
#   Path("a") / "b" / "c.txt"
#   Path.cwd()   Path.home()   Path(__file__)
#
# 解析：
#   p.name / p.stem / p.suffix / p.parent / p.parts
#   p.with_name("...") / p.with_suffix(".txt") / p.with_stem("...")
#
# 状态：
#   p.exists() / is_file() / is_dir() / stat()
#
# 遍历：
#   p.iterdir()         直接子项
#   p.glob("*.txt")     当前层匹配
#   p.rglob("*.txt")    递归匹配
#
# 读写：
#   p.read_text(encoding="utf-8")
#   p.write_text(content, encoding="utf-8")
#   p.read_bytes() / p.write_bytes()
#   with p.open() as f: ...    （大文件用这个）
#
# 增删改：
#   p.mkdir(parents=True, exist_ok=True)
#   p.rename(new_path)
#   p.unlink()      文件
#   p.rmdir()       空目录
#   shutil.rmtree(p)  非空目录
#
# 转换：
#   str(p)              平台原生
#   p.as_posix()        强制斜杠
#   p.resolve()         绝对路径
#
# 工程铁律：
#   - 永远不要拼路径字符串，用 Path / 操作
#   - 读写小文件 → read_text / write_text
#   - 读写大文件 → with p.open() 按行/按块
#   - 跨平台代码：as_posix() 统一格式
"""
"""
