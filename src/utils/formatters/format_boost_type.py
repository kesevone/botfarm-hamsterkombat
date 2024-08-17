from typing import Any, Optional

from src.hamster.enums import BoostType


def get_boost_name(boost_type: BoostType) -> Optional[str]:
    content: dict[str, Any] = {
        BoostType.EARN_PER_TAP: "Доход за тап",
        BoostType.MAX_TAPS: "Макс. кол-во тапов",
        BoostType.FULL_AVAILABLE_TAPS: "Текущее кол-во тапов",
    }
    return content[boost_type] if boost_type in content else None


def get_boost_description(boost_type: BoostType) -> Optional[str]:
    content: dict[str, Any] = {
        BoostType.EARN_PER_TAP: "Увеличивает доход монет за один тап.",
        BoostType.MAX_TAPS: "Увеличивает вашу энергию, максимальное кол-во тапов, которые вы можете использовать.",
        BoostType.FULL_AVAILABLE_TAPS: "Восстанавливает энергию, максимальное кол-во тапов, которые вы можете использовать. Есть задержка.",
    }
    return content[boost_type] if boost_type in content else None
