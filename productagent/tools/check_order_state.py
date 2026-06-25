from typing import Any


MOCK_ORDERS: dict[str, dict[str, Any]] = {
    "order_001": {
        "user_id": "user_001",
        "order_status": "delivered",
        "payment_status": "paid",
        "refundable": False,
        "notes": "Order is delivered. Do not promise a refund by default; check the refund policy first.",
    },
    "order_002": {
        "user_id": "user_002",
        "order_status": "pending_delivery",
        "payment_status": "paid",
        "refundable": True,
        "notes": "Order is paid but not delivered. It can enter refund policy review.",
    },
    "order_003": {
        "user_id": "user_003",
        "order_status": "unpaid",
        "payment_status": "unpaid",
        "refundable": False,
        "notes": "Order is unpaid. No refund is needed; ask the user to check payment status.",
    },
}


def check_order_state(order_id: str | None = None, user_id: str | None = None) -> dict[str, Any]:
    """Return deterministic local mock order state."""

    order_key = order_id or _first_order_for_user(user_id)
    if not order_key or order_key not in MOCK_ORDERS:
        return {
            "order_id": order_id,
            "user_id": user_id,
            "found": False,
            "order_status": "unknown",
            "payment_status": "unknown",
            "refundable": False,
            "notes": "Order was not found. Verify order information before giving a conclusion.",
        }

    order = MOCK_ORDERS[order_key]
    return {
        "order_id": order_key,
        "user_id": order["user_id"],
        "found": True,
        "order_status": order["order_status"],
        "payment_status": order["payment_status"],
        "refundable": order["refundable"],
        "notes": order["notes"],
    }


def _first_order_for_user(user_id: str | None) -> str | None:
    if not user_id:
        return None
    for order_id, order in MOCK_ORDERS.items():
        if order["user_id"] == user_id:
            return order_id
    return None
