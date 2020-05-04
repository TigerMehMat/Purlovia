from pathlib import PurePosixPath
from typing import *
from typing import cast

from ark.asset import find_dcsc
from ark.overrides import OverrideSettings, get_overrides_for_species
from ark.types import PrimalDinoCharacter
from ark.variants import adjust_name_from_variants, get_variants_from_assetname, get_variants_from_species
from automate.hierarchy_exporter import ExportFileModel, ExportModel, Field, JsonHierarchyExportStage
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.properties import FloatProperty, StringLikeProperty
from ue.proxy import UEProxyStructure
from ue.utils import clean_double as cd
from utils.log import get_logger

from .flags import gather_flags
from .species.attacks import AttackData, gather_attack_data
from .species.movement import MovementModes, gather_movement_data

__all__ = [
    'SpeciesStage',
]

logger = get_logger(__name__)

OUTPUT_FLAGS = (
    'bAllowCarryFlyerDinos',
    'bAllowFlyerLandedRider',
    'bAllowMountedWeaponry',
    'bAllowRiding',
    'bAllowRidingInWater',
    'bCanBeDragged',
    'bCanBeTorpid',
    'bCanDrag',
    'bCanMountOnHumans',
    'bDoStepDamage',
    'bFlyerAllowRidingInCaves',
    'bIsAmphibious',
    'bIsBigDino',
    'bIsBossDino',
    'bIsCarnivore',
    'bIsCorrupted',
    'bIsFlyerDino',
    'bIsNPC',
    'bIsRaidDino',
    'bIsRobot',
    'bIsWaterDino',
    'bPreventCharacterBasing',
    'bPreventEnteringWater',
    'bPreventNeuter',

    # Other related stuff not included:
    # bCanRun/Jump/Walk/Crouch/etc - covered with the movement speed section
    # bUseColorization - in future color data will cover this
    # bCanHaveBaby/bUseBabyGestation - add breeding section
)


class FallingData(ExportModel):
    dmgMult: FloatProperty = Field(..., title="Damage multiplier")
    maxSpeed: FloatProperty = Field(..., title="Max speed")


class Species(ExportModel):
    name: Optional[str] = Field(
        None,
        description="Descriptive name",
    )
    blueprintPath: str = Field(
        ...,
        alias='bp',
        title="Full blueprint path",
    )

    dinoNameTag: Optional[StringLikeProperty] = Field(
        None,
        title="Dino name tag",
        description="Only known use is saddle compatibility",
    )
    customTag: Optional[StringLikeProperty] = Field(
        None,
        title="Custom tag",
        description="",
    )
    targetingTeamName: Optional[StringLikeProperty] = Field(
        None,
        title="Targeting team name",
        description="Prevent friendly fire with creatures in the same team",
    )

    mass: Optional[FloatProperty] = Field(
        None,
        description="Physics mass, used as a limit in some immobilisation systems",
    )
    dragWeight: Optional[FloatProperty] = Field(
        None,
        title="Drag weight",
        description="Apparent weight for many game systems including carrying and boss arena entry limits",
    )

    variants: Optional[Tuple[str, ...]] = Field(
        tuple(),
        description="List of relevant variant names",
    )
    flags: Optional[List[str]] = Field(
        list(),
        description="Relevant boolean flags that are True for this species",
    )

    falling: Optional[FallingData]
    movementW: Optional[MovementModes] = Field(None, title="Movement (wild)")
    movementD: Optional[MovementModes] = Field(None, title="Movement (domesticated)")
    attack: Optional[AttackData]


class SpeciesExportModel(ExportFileModel):
    species: List[Species]

    class Config:
        title = "Species data for the Wiki"


def should_skip_from_variants(variants: Set[str], overrides: OverrideSettings) -> bool:
    skip_variants = set(name for name, use in overrides.variants_to_skip_export.items() if use)
    return bool(variants & skip_variants)


class SpeciesStage(JsonHierarchyExportStage):
    def get_name(self) -> str:
        return 'species'

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_format_version(self):
        return "1"

    def get_ue_type(self):
        return PrimalDinoCharacter.get_ue_type()

    def get_schema_model(self):
        return SpeciesExportModel

    def extract(self, proxy: UEProxyStructure) -> Any:
        species: PrimalDinoCharacter = cast(PrimalDinoCharacter, proxy)

        asset: UAsset = proxy.get_source().asset
        assert asset.assetname and asset.default_class
        modid: Optional[str] = self.manager.loader.get_mod_id(asset.assetname)
        overrides = get_overrides_for_species(asset.assetname, modid)

        if _should_skip_species(species, overrides):
            return None

        name = str(species.DescriptiveName[0])

        variants = get_variants_from_assetname(asset.assetname, overrides) | get_variants_from_species(species)
        if variants:
            if should_skip_from_variants(variants, overrides):
                return None

            name = adjust_name_from_variants(name, variants, overrides)

        out = Species(blueprintPath=asset.default_class.fullname)
        out.name = name
        out.dinoNameTag = species.DinoNameTag[0]
        out.customTag = species.CustomTag[0]
        out.targetingTeamName = species.TargetingTeamNameOverride[0]
        out.mass = species.CharacterMovement[0].Mass[0]
        out.dragWeight = species.DragWeight[0]

        if variants:
            out.variants = tuple(sorted(variants))

        out.flags = gather_flags(species, OUTPUT_FLAGS)

        out.falling = FallingData(
            dmgMult=species.FallDamageMultiplier[0],
            maxSpeed=species.MaxFallSpeed[0],
        )

        movement = gather_movement_data(species)
        out.movementW = movement.movementW
        out.movementD = movement.movementD
        out.attack = gather_attack_data(species)

        return out


def _should_skip_species(species: PrimalDinoCharacter, overrides: OverrideSettings):
    if overrides.skip_export:
        return True

    if not species.has_override('DescriptiveName'):
        return True

    return False
