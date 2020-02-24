from typing import Any, Dict, cast

from ark.types import PrimalItem
from export.wiki.types import ShooterWeapon, ShooterWeapon_Instant, ShooterWeapon_Melee
from ue.gathering import gather_properties


def gather_weapon_values(item: PrimalItem) -> Dict[str, Any]:
    v: Dict[str, Any] = dict()
    if not 'WeaponTemplate' in item or not item.WeaponTemplate[0].value.value:
        return v

    template_ref = item.WeaponTemplate[0]
    template = item.get_source().asset.loader.load_related(template_ref).default_export

    if not template:
        return v

    weapon: ShooterWeapon = gather_properties(template)

    v['blueprintPath'] = template_ref
    v['equipTime'] = weapon.EquipTime[0]
    v['supportsShields'] = weapon.bSupportsOffhandShield[0]

    damage: Dict[str, Any] = dict()
    if isinstance(weapon, ShooterWeapon_Melee):
        melee = cast(ShooterWeapon_Melee, weapon)
        damage['raw'] = melee.MeleeDamageAmount[0]
        damage['type'] = melee.MeleeDamageType[0]
    elif isinstance(weapon, ShooterWeapon_Instant):
        instant_config = weapon.InstantConfig[0].as_dict()
        damage['raw'] = instant_config['HitDamage']
        #damage['type'] = instant_config['DamageType']

    v['damage'] = damage

    return dict(weapon=v)
