r"""
标准库 03：datetime
─────────────────────────────────────────
内容：
1. date / time / datetime ── 三个核心类
2. timedelta ── 时间差
3. now / utcnow / 时区基础
4. zoneinfo ── 现代时区方案（Python 3.9+）
5. strftime / strptime ── 格式化与解析
6. ISO 8601 格式
7. 实战：年龄计算、工作日判断、时间区间
"""

from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo


# ══════════════════════════════════════════════════════
# 1. 三个核心类
# ══════════════════════════════════════════════════════

# date：只有日期（年月日）
d = date(2026, 5, 25)
print("── date ──")
print(d)                # 2026-05-25
print(d.year, d.month, d.day)
print(d.weekday())      # 0 = 周一，6 = 周日


# time：只有时间（时分秒）
t = time(14, 30, 0)
print("\n── time ──")
print(t)                # 14:30:00


# datetime：日期+时间
dt = datetime(2026, 5, 25, 14, 30, 0)
print("\n── datetime ──")
print(dt)               # 2026-05-25 14:30:00
print(dt.date())        # 提取出 date 部分
print(dt.time())        # 提取出 time 部分


# 当前时间
print("\n── 当前时间 ──")
print(datetime.now())            # 本地时间（不带时区！）
print(datetime.now(timezone.utc)) # UTC 时间（带时区）
print(date.today())               # 今天


# ══════════════════════════════════════════════════════
# 2. timedelta ── 时间差
# ══════════════════════════════════════════════════════
# 表示"两个时间点之间的距离"或"时长"

td = timedelta(days=7, hours=3, minutes=30)
print("\n── timedelta ──")
print(td)                  # 7 days, 3:30:00
print(td.total_seconds())  # 折算成秒：624600.0


# datetime ± timedelta = datetime
now = datetime(2026, 5, 25, 12, 0, 0)
print(now + timedelta(days=7))     # 一周后
print(now - timedelta(hours=3))    # 3 小时前
print(now + timedelta(weeks=2))    # 两周后


# datetime - datetime = timedelta
deadline = datetime(2026, 12, 31)
remaining = deadline - now
print(f"距离 deadline 还有 {remaining.days} 天")


# 注意：timedelta 不支持 month / year（月份天数不固定）
# 想加"几个月"用 dateutil.relativedelta（第三方库）


# ══════════════════════════════════════════════════════
# 3. 时区：naive vs aware
# ══════════════════════════════════════════════════════
# Python datetime 分两种：
#   naive    没有时区信息（datetime(2026,5,25,12,0)）
#   aware    带时区信息（datetime(..., tzinfo=...)）
#
# 工程铁律：
#   - 任何能见日的时间都应该是 aware（带时区）
#   - 永远不要混用 naive 和 aware
#   - 内部存储一律用 UTC，展示时再转本地

naive = datetime.now()
aware_utc = datetime.now(timezone.utc)

print("\n── naive vs aware ──")
print(f"  naive:    {naive}              tzinfo={naive.tzinfo}")
print(f"  aware:    {aware_utc}    tzinfo={aware_utc.tzinfo}")

# 两者不能直接比较 / 计算
# print(naive > aware_utc)    # ❌ TypeError


# ══════════════════════════════════════════════════════
# 4. zoneinfo ── 现代时区（Python 3.9+）
# ══════════════════════════════════════════════════════

shanghai = ZoneInfo("Asia/Shanghai")
new_york = ZoneInfo("America/New_York")

now_sh = datetime.now(shanghai)
now_ny = datetime.now(new_york)

print("\n── zoneinfo 多时区 ──")
print(f"  上海: {now_sh}")
print(f"  纽约: {now_ny}")


# 时区转换：astimezone()
utc_now = datetime.now(timezone.utc)
print(f"  UTC:  {utc_now}")
print(f"  → 上海: {utc_now.astimezone(shanghai)}")
print(f"  → 纽约: {utc_now.astimezone(new_york)}")


# 给 naive 时间"加上"时区（不是转换，是声明）
local = datetime(2026, 5, 25, 12, 0)
local_with_tz = local.replace(tzinfo=shanghai)
print(f"\n  原来 naive: {local}")
print(f"  加上时区: {local_with_tz}")
print(f"  转 UTC: {local_with_tz.astimezone(timezone.utc)}")


# ══════════════════════════════════════════════════════
# 5. 格式化：strftime
# ══════════════════════════════════════════════════════
# 把 datetime 格式化成字符串

dt = datetime(2026, 5, 25, 14, 30, 45)

print("\n── strftime ──")
print(dt.strftime("%Y-%m-%d"))               # 2026-05-25
print(dt.strftime("%Y-%m-%d %H:%M:%S"))      # 2026-05-25 14:30:45
print(dt.strftime("%Y年%m月%d日 %H时%M分"))  # 中文
print(dt.strftime("%A, %B %d %Y"))           # Monday, May 25 2026
print(dt.strftime("%a %b %d"))               # 缩写


# 常用格式符（不全，按需查）：
#   %Y  4 位年        %y  2 位年
#   %m  月（01-12）   %d  日
#   %H  时（24h）     %I  时（12h）
#   %M  分            %S  秒
#   %A  星期全名      %a  星期缩写
#   %B  月份全名      %b  月份缩写
#   %p  AM/PM         %z  时区偏移


# ══════════════════════════════════════════════════════
# 6. 解析：strptime
# ══════════════════════════════════════════════════════
# 把字符串解析成 datetime（strftime 的反操作）

s = "2026-05-25 14:30:45"
dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
print("\n── strptime ──")
print(dt)
print(type(dt))


# 常见格式
print(datetime.strptime("2026/05/25", "%Y/%m/%d"))
print(datetime.strptime("25 May 2026", "%d %b %Y"))


# ══════════════════════════════════════════════════════
# 7. ISO 8601 ── 现代标准格式
# ══════════════════════════════════════════════════════
# 2026-05-25T14:30:45+08:00 这种形式

dt = datetime(2026, 5, 25, 14, 30, 45, tzinfo=ZoneInfo("Asia/Shanghai"))

print("\n── ISO 8601 ──")
print(dt.isoformat())                        # 2026-05-25T14:30:45+08:00

# 解析（Python 3.11+ 支持完整 ISO）
parsed = datetime.fromisoformat("2026-05-25T14:30:45+08:00")
print(parsed)


# ISO 8601 是最通用的交换格式：
#   - JSON / API 接口默认用这个
#   - 数据库存这种格式不会出错
#   - 不同语言都能解析
#
# 工程铁律：
#   存储 / 传输 → ISO 8601 字符串
#   显示 → 按需 strftime 美化


# ══════════════════════════════════════════════════════
# 8. 实战 1：年龄计算
# ══════════════════════════════════════════════════════

def calc_age(birth: date, today: date | None = None) -> int:
    """精确算年龄（考虑生日是否过了）"""
    today = today or date.today()
    age = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        age -= 1
    return age


print("\n── 年龄计算 ──")
print(calc_age(date(1995, 8, 15), today=date(2026, 5, 25)))    # 30（生日还没到）
print(calc_age(date(1995, 5, 25), today=date(2026, 5, 25)))    # 31


# ══════════════════════════════════════════════════════
# 9. 实战 2：判断工作日 / 周末
# ══════════════════════════════════════════════════════

def is_weekend(d: date) -> bool:
    return d.weekday() >= 5      # 周六=5，周日=6


def next_workday(d: date) -> date:
    while is_weekend(d := d + timedelta(days=1)):
        pass
    return d


print("\n── 工作日 ──")
today = date(2026, 5, 22)        # 周五
print(f"  {today}: 周末? {is_weekend(today)}")
print(f"  下个工作日: {next_workday(today)}")    # 跳过周末，到下周一


# ══════════════════════════════════════════════════════
# 10. 实战 3：时间区间生成
# ══════════════════════════════════════════════════════

def date_range(start: date, end: date, step_days: int = 1):
    """生成 [start, end] 之间的日期序列"""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=step_days)


print("\n── 日期区间 ──")
for d in date_range(date(2026, 5, 25), date(2026, 5, 28)):
    print(f"  {d} ({d.strftime('%A')})")


# ══════════════════════════════════════════════════════
# 11. 实战 4：把 epoch 时间戳转 datetime
# ══════════════════════════════════════════════════════

import time

ts = time.time()                     # 当前 epoch 秒
print(f"\n── 时间戳互转 ──")
print(f"  epoch: {ts}")

# 时间戳 → datetime
dt = datetime.fromtimestamp(ts, tz=timezone.utc)
print(f"  UTC:   {dt}")

# datetime → 时间戳
print(f"  back to epoch: {dt.timestamp()}")


# 注意陷阱：
#   datetime.fromtimestamp(ts)         返回本地时区的 naive datetime（不推荐）
#   datetime.fromtimestamp(ts, tz=...)  返回 aware datetime（推荐）
#   datetime.utcfromtimestamp(ts)      被 deprecated，别用


# ══════════════════════════════════════════════════════
# 12. 速查
# ══════════════════════════════════════════════════════
#
# 三个核心类：
#   date(y, m, d)           日期
#   time(h, m, s)           时间
#   datetime(y, m, d, h, m, s, tzinfo=...)   日期+时间
#
# 时长：
#   timedelta(days=N, hours=N, ...)
#   datetime - datetime = timedelta
#   datetime + timedelta = datetime
#
# 时区（Python 3.9+）：
#   from zoneinfo import ZoneInfo
#   tz = ZoneInfo("Asia/Shanghai")
#   dt.astimezone(tz)        转换
#   dt.replace(tzinfo=tz)    给 naive 加上时区（声明，不是转换）
#
# 字符串：
#   dt.strftime("%Y-%m-%d %H:%M:%S")     格式化
#   datetime.strptime(s, "...")          解析
#   dt.isoformat()                       ISO 8601 字符串
#   datetime.fromisoformat("...")        从 ISO 解析
#
# 时间戳：
#   datetime.fromtimestamp(ts, tz=timezone.utc)
#   dt.timestamp()
#
# 工程铁律：
#   - 永远用 aware datetime（带时区）
#   - 内部存储 UTC，展示时再转本地
#   - 跨系统传输用 ISO 8601
#   - 不要用 utcnow / utcfromtimestamp（已 deprecated）
#   - 复杂日历运算（"加 3 个月"）→ 第三方库 dateutil
"""
"""
