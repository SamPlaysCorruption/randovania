import dataclasses
import uuid
from unittest.mock import MagicMock

from PySide6 import QtCore

from randovania.games.dread.gui.preset_settings.dread_energy_tab import PresetDreadEnergy
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.interface_common.preset_editor import PresetEditor


def test_toggle_immediate_parts(skip_qtbot, dread_game_description, preset_manager):
    game = dread_game_description.game
    base = preset_manager.default_preset_for_game(game).get_preset()
    preset = dataclasses.replace(base, uuid=uuid.UUID('b41fde84-1f57-4b79-8cd6-3e5a78077fa6'))
    base_configuration = preset.configuration
    options = MagicMock()
    assert isinstance(base_configuration, DreadConfiguration)

    tab = PresetDreadEnergy(editor := PresetEditor(preset, options), dread_game_description, MagicMock())
    skip_qtbot.addWidget(tab)
    tab.on_preset_changed(preset)

    assert tab.energy_tank_capacity_spin_box.isEnabled()

    skip_qtbot.mouseClick(tab.immediate_energy_parts_check, QtCore.Qt.LeftButton)
    tab.on_preset_changed(editor.create_custom_preset_with())

    configuration = editor.configuration
    assert isinstance(configuration, DreadConfiguration)
    assert configuration.immediate_energy_parts != base_configuration.immediate_energy_parts
    assert not tab.energy_tank_capacity_spin_box.isEnabled()
