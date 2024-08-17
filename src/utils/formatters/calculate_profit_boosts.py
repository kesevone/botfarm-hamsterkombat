from src.database.models import DBAccount, DBAccountUpgrade
from src.hamster import HamsterUpgrade


def calculate_profit_upgrades(
    account: DBAccount, upgrades: list[DBAccountUpgrade], sections: list[str]
) -> list[HamsterUpgrade]:
    profit_upgrades = []

    for section in sections:
        best_upgrade = None
        min_ratio = float("inf")

        for upgrade in upgrades:
            if (
                upgrade.section == section
                and upgrade.cooldown_seconds == 0
                and upgrade.is_active
                and not upgrade.is_expired
                and upgrade.profit_per_hour > 0
                and 0 < upgrade.price <= account.balance_coins
            ):
                ratio = round(upgrade.price / upgrade.profit_per_hour, 2)
                if ratio < min_ratio:
                    min_ratio = ratio
                    best_upgrade = upgrade

        if best_upgrade:
            profit_upgrades.append(
                HamsterUpgrade(
                    id=best_upgrade.type,
                    section=best_upgrade.section,
                    level=best_upgrade.level,
                    price=best_upgrade.price,
                    profitPerTime=min_ratio,
                    profitPerTap=best_upgrade.profit_per_hour,
                    isExpired=best_upgrade.is_expired,
                    isAvailable=best_upgrade.is_active,
                    lastUpgradeAt=best_upgrade.last_upgrade_at,
                )
            )

    unique_upgrades = []
    for upgrade in profit_upgrades:
        if upgrade not in unique_upgrades:
            unique_upgrades.append(upgrade)

    return unique_upgrades
