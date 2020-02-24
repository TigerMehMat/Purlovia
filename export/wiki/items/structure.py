from typing import Any, Dict, List, cast

from ark.types import PrimalItem
from export.wiki.stage_species import _clean_flag_name
from export.wiki.types import PrimalStructure
from ue.gathering import gather_properties

OUTPUT_FLAGS = (
    'bCanDemolish',
    'bCanBeRepaired',
    'bPreventPlacementInWater',
)


def gather_structure_values(item: PrimalItem) -> Dict[str, Any]:
    v: Dict[str, Any] = dict()
    if not 'StructureToBuild' in item or not item.StructureToBuild[0].value.value:
        return v

    template_ref = item.StructureToBuild[0]
    template = item.get_source().asset.loader.load_related(template_ref).default_export
    proxy: PrimalStructure = gather_properties(template)

    v['blueprintPath'] = template_ref
    v['name'] = proxy.DescriptiveName[0]
    if proxy.bUsesHealth[0]:
        v['health'] = proxy.Health[0]
    v['flags'] = _gather_flags(proxy)
    v['decayMult'] = proxy.DecayDestructionPeriodMultiplier[0]

    return dict(structure=v)


def _gather_flags(structure: PrimalStructure) -> List[str]:
    result = [_clean_flag_name(field) for field in OUTPUT_FLAGS if structure.get(field, fallback=False)]
    return result
