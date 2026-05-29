"""
dataclass 工程实战：订单取消流程
─────────────────────────────────────────
演示一个真实项目里典型的对象分层：

    配置层 → 枚举 → 领域对象 → 命令 → 事件 → 处理结果

把 enum + dataclass 的所有特性串成一个完整流程。
"""

from dataclasses import dataclass, field, replace, asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4


# ══════════════════════════════════════════════════════
# 1. 配置层 ── frozen 保证启动后不被改
# ══════════════════════════════════════════════════════

@dataclass(frozen=True)
class AppConfig:
    db_url: str
    refund_window_days: int = 7         # 几天内可以取消订单
    auto_refund: bool = True


# ══════════════════════════════════════════════════════
# 2. 枚举 ── 把"有限状态"打包成类型
# ══════════════════════════════════════════════════════

class OrderStatus(Enum):
    PENDING = "pending"          # 待支付
    PAID = "paid"                # 已支付
    SHIPPED = "shipped"          # 已发货
    DELIVERED = "delivered"      # 已送达
    CANCELLED = "cancelled"      # 已取消


class CancelReason(Enum):
    USER_REQUEST = "user_request"
    PAYMENT_FAILED = "payment_failed"
    OUT_OF_STOCK = "out_of_stock"


# ══════════════════════════════════════════════════════
# 3. 领域对象 ── 业务方法和数据绑在一起
# ══════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class OrderItem:
    """订单条目：不可变值对象"""
    sku: str
    name: str
    price: Decimal
    quantity: int

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity


@dataclass(slots=True)
class Order:
    """订单：可变实体（状态会变）"""
    id: str
    customer_id: str
    items: list[OrderItem]
    status: OrderStatus
    created_at: datetime
    cancelled_at: datetime | None = None

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    def can_cancel(self, config: AppConfig) -> tuple[bool, str]:
        """业务规则集中在领域对象里，调用方拿到的是确定答案"""
        if self.status == OrderStatus.CANCELLED:
            return False, "订单已取消"
        if self.status == OrderStatus.DELIVERED:
            return False, "已送达订单不能取消"
        days = (datetime.now() - self.created_at).days
        if days > config.refund_window_days:
            return False, f"超过 {config.refund_window_days} 天取消窗口"
        return True, ""


# ══════════════════════════════════════════════════════
# 4. 命令对象 ── 描述"想做什么"，frozen 防篡改
# ══════════════════════════════════════════════════════

@dataclass(frozen=True, kw_only=True)
class CancelOrderCommand:
    order_id: str
    operator_id: str
    reason: CancelReason
    note: str = ""


# ══════════════════════════════════════════════════════
# 5. 事件对象 ── 描述"发生了什么"，frozen 是事实
# ══════════════════════════════════════════════════════

@dataclass(frozen=True, kw_only=True)
class OrderCancelledEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    order_id: str
    refund_amount: Decimal
    reason: CancelReason
    occurred_at: datetime = field(default_factory=datetime.now)


# ══════════════════════════════════════════════════════
# 6. 处理结果 ── 替代裸 tuple，调用方好读
# ══════════════════════════════════════════════════════

@dataclass
class HandlerResult:
    ok: bool
    event: OrderCancelledEvent | None = None
    error: str | None = None


# ══════════════════════════════════════════════════════
# 7. 业务处理函数 ── 把上面这些串起来
# ══════════════════════════════════════════════════════

def cancel_order(
    order: Order,
    cmd: CancelOrderCommand,
    config: AppConfig,
) -> tuple[Order, HandlerResult]:
    """
    返回：(更新后的订单, 处理结果)
    特意不修改入参 order，返回新对象，方便测试和回滚
    """
    # 1) 校验
    can, why = order.can_cancel(config)
    if not can:
        return order, HandlerResult(ok=False, error=why)

    # 2) 用 replace 生成新订单（不修改原对象）
    new_order = replace(
        order,
        status=OrderStatus.CANCELLED,
        cancelled_at=datetime.now(),
    )

    # 3) 发出事件
    event = OrderCancelledEvent(
        order_id=order.id,
        refund_amount=order.total if config.auto_refund else Decimal("0"),
        reason=cmd.reason,
    )

    return new_order, HandlerResult(ok=True, event=event)


# ══════════════════════════════════════════════════════
# 8. 跑一遍完整流程
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    # 启动配置（应用生命周期里只创建一次）
    config = AppConfig(
        db_url="postgresql://localhost/shop",
        refund_window_days=7,
        auto_refund=True,
    )
    print("【配置】", config)

    # 模拟从数据库读出来一个订单
    order = Order(
        id="ORD-1001",
        customer_id="USR-42",
        items=[
            OrderItem(sku="A001", name="Python 入门", price=Decimal("59"), quantity=1),
            OrderItem(sku="B007", name="实战教程", price=Decimal("89"), quantity=2),
        ],
        status=OrderStatus.PAID,
        created_at=datetime.now(),
    )
    print("\n【订单】", order)
    print(f"  总计: ¥{order.total}")

    # 用户发起取消
    cmd = CancelOrderCommand(
        order_id=order.id,
        operator_id="USR-42",
        reason=CancelReason.USER_REQUEST,
        note="买错了",
    )
    print("\n【命令】", cmd)

    # 处理
    new_order, result = cancel_order(order, cmd, config)

    if result.ok:
        print("\n【结果】 取消成功")
        print("  新状态:", new_order.status)
        print("  事件:", result.event)
        print("  退款金额: ¥", result.event.refund_amount)

        # 序列化事件准备发到消息队列（asdict 递归转）
        import json
        payload = asdict(result.event)
        # decimal/datetime/enum 需要自定义序列化，这里简化处理
        payload["refund_amount"] = str(payload["refund_amount"])
        payload["occurred_at"] = payload["occurred_at"].isoformat()
        payload["reason"] = payload["reason"].value
        print("\n【消息队列 payload】")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("\n【结果】 取消失败:", result.error)

    # 验证：原 order 没被改（frozen 不需要，但 slots 类靠 replace 保证）
    print("\n【验证】 原订单状态未变:", order.status)
