r"""
异常第一层：基础
─────────────────────────────────────────
内容：
1. try / except / else / finally 的真实语义
2. 异常对象的属性（args / __cause__ / __context__）
3. 多分支捕获 + 多类型 except
4. raise 重新抛出
5. Python 内置异常的继承体系
"""


# ══════════════════════════════════════════════════════
# 1. try/except 的最简形式
# ══════════════════════════════════════════════════════

def safe_divide(a: float, b: float) -> float | None:
    try:
        return a / b
    except ZeroDivisionError:
        print("  除以 0 了")
        return None


print("── 基础 try/except ──")
print(safe_divide(10, 2))   # 5.0
print(safe_divide(10, 0))   # None


# ══════════════════════════════════════════════════════
# 2. 完整版：try / except / else / finally
# ══════════════════════════════════════════════════════
# 四个块的执行时机：
#   try     总是执行
#   except  仅在 try 抛了对应异常时
#   else    仅在 try 没抛异常时
#   finally 永远执行（不管是否异常、是否 return）

def demo(x):
    try:
        result = 100 / x
    except ZeroDivisionError:
        print("  except 块：除以 0")
        return "error"
    else:
        print(f"  else 块：成功，结果={result}")
        return result
    finally:
        print("  finally 块：清理")


print("\n── 四块完整版 ──")
print("  -- 正常 --")
demo(2)
print("  -- 异常 --")
demo(0)


# 关键观察：finally 即使在 return 之后也会执行
# 这是它"保证清理"的能力来源（资源关闭、锁释放等）


# ══════════════════════════════════════════════════════
# 3. 多分支：不同异常不同处理
# ══════════════════════════════════════════════════════

def parse_int(s: str) -> int | None:
    try:
        return int(s)
    except ValueError:
        print(f"  无法转成整数: {s!r}")
        return None
    except TypeError:
        print(f"  类型错了: {type(s).__name__}")
        return None


print("\n── 多分支 ──")
parse_int("abc")    # ValueError
parse_int(None)     # TypeError


# 多个异常合并捕获（共享处理逻辑）
def parse_int_v2(s):
    try:
        return int(s)
    except (ValueError, TypeError) as e:
        print(f"  解析失败: {type(e).__name__}: {e}")
        return None


parse_int_v2("xyz")
parse_int_v2(None)


# ══════════════════════════════════════════════════════
# 4. 异常对象 ── 不只是字符串
# ══════════════════════════════════════════════════════

print("\n── 异常对象 ──")
try:
    int("hello")
except ValueError as e:
    print(f"  类型: {type(e).__name__}")
    print(f"  消息: {e}")
    print(f"  args: {e.args}")           # 构造时的所有参数
    print(f"  isinstance Exception: {isinstance(e, Exception)}")


# ══════════════════════════════════════════════════════
# 5. raise ── 主动抛出
# ══════════════════════════════════════════════════════

def set_age(age: int):
    if age < 0 or age > 150:
        raise ValueError(f"非法年龄: {age}")
    if not isinstance(age, int):
        raise TypeError(f"年龄必须是 int，得到 {type(age).__name__}")
    return age


print("\n── 主动 raise ──")
try:
    set_age(-5)
except ValueError as e:
    print(f"  捕获到: {e}")


# ══════════════════════════════════════════════════════
# 6. 重新抛出（re-raise）
# ══════════════════════════════════════════════════════
# 想"先记日志，再让异常继续向上传"，用裸 raise

def process(x):
    try:
        return 100 / x
    except ZeroDivisionError:
        print("  [日志] 发生除零，但我处理不了，向上抛")
        raise                        # ← 不带参数的 raise，重抛当前异常


print("\n── re-raise ──")
try:
    process(0)
except ZeroDivisionError as e:
    print(f"  外层捕获: {type(e).__name__}")


# ══════════════════════════════════════════════════════
# 7. Python 内置异常的继承体系（重点！）
# ══════════════════════════════════════════════════════
#
# BaseException                     ← 所有异常的根
#   ├── SystemExit                  ← sys.exit() 触发
#   ├── KeyboardInterrupt           ← Ctrl+C
#   ├── GeneratorExit               ← 生成器关闭
#   └── Exception                   ← 99% 用户异常的祖先（捕获这个就够）
#       ├── ArithmeticError
#       │   ├── ZeroDivisionError
#       │   └── OverflowError
#       ├── LookupError
#       │   ├── IndexError          ← list[100] 越界
#       │   └── KeyError            ← dict["missing"] 找不到
#       ├── TypeError
#       ├── ValueError
#       ├── OSError
#       │   ├── FileNotFoundError
#       │   ├── PermissionError
#       │   └── ConnectionError
#       ├── RuntimeError
#       ├── StopIteration           ← 生成器结束
#       └── ... 等等
#
# 关键规则：
#   - except SomeClass 会捕获 SomeClass 及其所有子类
#   - except Exception 捕获用户异常，但不捕 KeyboardInterrupt
#   - except BaseException ← 一般别用，会拦掉 Ctrl+C 退出


# 演示：捕获基类能抓到所有子类
print("\n── 继承捕获 ──")
for case in [lambda: 1/0, lambda: [][0], lambda: {}["x"]]:
    try:
        case()
    except ArithmeticError as e:
        print(f"  ArithmeticError 抓到: {type(e).__name__}: {e}")
    except LookupError as e:
        print(f"  LookupError 抓到: {type(e).__name__}: {e}")


# ══════════════════════════════════════════════════════
# 8. 永远别 except: pass
# ══════════════════════════════════════════════════════
# 几个反模式：

# ❌ 反例 1：吞掉所有异常（包括 KeyboardInterrupt 这种）
# try:
#     ...
# except:           # ← 不指定类型 = except BaseException
#     pass          # ← 还把异常吞了，调试地狱
#

# ❌ 反例 2：捕了基类却什么都不做
# try:
#     ...
# except Exception:
#     pass

# ✅ 正确：要么处理、要么记日志再 raise、要么转成业务异常

import logging

def good_pattern(x):
    try:
        return 100 / x
    except ZeroDivisionError:
        logging.warning("业务降级：除零")
        return 0                          # 明确的降级值
    # 其他异常不接：让它向上抛


# ══════════════════════════════════════════════════════
# 9. except 的"粒度"：从精确到泛化
# ══════════════════════════════════════════════════════
#
# 粒度从细到粗：
#
#   except FileNotFoundError   ← 最准，意图清楚
#   except OSError              ← 文件系统相关都接
#   except Exception           ← 用户层异常都接
#   except BaseException        ← 系统级也接（几乎不用）
#
# 工程铁律：
#   接得越精确越好。except Exception 是兜底，不该是默认选择


# ══════════════════════════════════════════════════════
# 10. 速查
# ══════════════════════════════════════════════════════
#
# 四块语义：
#   try     ── 主体
#   except  ── try 抛异常时执行
#   else    ── try 正常完成时执行
#   finally ── 永远执行（清理）
#
# 抛出：
#   raise ValueError("...")     新抛
#   raise                       重抛当前异常
#   raise NewError(...) from e  抛新异常并保留原因（下一章详讲）
#
# 多分支：
#   except (A, B) as e:         多类型合并
#   except A: ... except B:     不同处理
#
# 异常对象：
#   e.args    构造时的所有位置参数
#   str(e)    人类可读消息
#
# 工程铁律：
#   - 永远不写 except: pass
#   - 接得越精确越好
#   - except Exception 只在"程序的最外层"用作兜底
"""
"""
