from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set, cast

from ark.overrides import get_overrides_for_map
from automate.exporter import ExportManager, ExportRoot, ExportStage
from automate.jsonutils import save_json_if_changed
from automate.version import createExportVersion
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.utils import sanitise_output

from .types import SoundCue

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'ExplorerNoteStage',
]


class ExplorerNoteStage(ExportStage):
    def get_format_version(self) -> str:
        return '1'

    def get_skip(self) -> bool:
        return not self.manager.config.export_wiki.ExportExplorerNotes

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def extract_core(self, path: Path):
        '''Perform extraction for core (non-mod) data.'''
        # Core versions are based on the game version and build number
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.arkman.getGameBuildId())  # type: ignore

        pgd: UAsset = self.manager.loader['/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP']
        pgd_export = pgd.default_export
        if not pgd_export:
            return
        note_entries = pgd_export.properties.get_property('ExplorerNoteEntries')

        format_version = self.get_format_version()
        output: Dict[str, Any] = dict(version=version, format=format_version, explorerNotes=[])

        for entry in note_entries.values:
            d = decode_note_entry(self.manager.loader, entry.as_dict())
            output['explorerNotes'].append(d)

        output = sanitise_output(output)
        save_json_if_changed(output, (path / 'explorer_notes.json'), self.get_use_pretty())

    def extract_mod(self, path, modid):
        # Mods cannot add new notes without overriding the core.
        ...


EXPLORER_NOTE_TYPE_MAP = {
    0: 'Helena',
    1: 'Rockwell',
    2: 'Mei Yin',
    3: 'Nerva',
    4: 'Bossier',
    6: 'Raia',
    7: 'Dahkeya',
    8: 'Grad Student',
    9: 'Diana',
    10: 'The One Who Waits',
    11: 'Santiago',
    12: 'HLN-A',
}


def decode_note_entry(loader, d):
    v = dict()
    type_id = int(d['ExplorerNoteType'])
    v['uiCategory'] = EXPLORER_NOTE_TYPE_MAP.get(type_id, type_id)
    v['title'] = d['ExplorerNoteDescription']

    dossier_tag = str(d['DossierTameableDinoNameTag'])
    if dossier_tag != 'None':
        v['dinoTag'] = dossier_tag

    v['graphics'] = dict(
        mesh=d['ExplorerNoteMesh'],
        texture=d['ExplorerNoteTexture'].values[0],
        icon=d['ExplorerNoteIcon'],
        iconMaterial=d['ExplorerNoteIconMaterial'],
    )

    audio = d['LocalizedAudio'].values
    if not audio:
        v['content'] = dict(en=dict(text=d['LocalizedSubtitle'], ))
    else:
        v['content'] = decode_note_audio_sets(loader, audio)

    return v


def decode_note_audio_sets(loader, d):
    v = dict()

    for struct in d:
        s = struct.as_dict()
        iso_code = str(s['TwoLetterISOLanguageName'])
        v[iso_code] = gather_data_from_sound_cue(loader, s)

    return v


def gather_data_from_sound_cue(loader, d):
    cue_ref = d['LocalizedSoundCue']
    v = dict(soundCue=cue_ref, text='')

    cue_asset = loader.load_related(cue_ref)
    cue_export = cue_asset.default_export
    if not cue_export:
        # TODO: Handle error.
        return None
    cue: SoundCue = cast(SoundCue, gather_properties(cue_export))

    subtitles = cue.get('Subtitles', fallback=None)
    texts = list()
    if subtitles:
        for subtitle in subtitles.values:
            subtitle_d = subtitle.as_dict()
            texts.append(str(subtitle_d['Text']))
    v['text'] = '\n'.join(texts)

    return v
