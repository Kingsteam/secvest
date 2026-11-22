"""Fork HW18: arming without a code, disarming only with one."""

from typing import Any

from homeassistant.components.alarm_control_panel.const import (
    AlarmControlPanelState,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
import pytest

from custom_components.secvest.api.models import PartitionState
from custom_components.secvest.const import CONF_ARM_WITHOUT_CODE

from .common import ROUND, Setup, arming_failed_events, call_panel, get_state
from .fake_panel import FakePanel
from .ha.common import MockConfigEntry

ARM_FREELY = {CONF_ARM_WITHOUT_CODE: True}


async def _code_arming(
    hass: HomeAssistant, entry: MockConfigEntry, value: bool | None = None
) -> Any:
    """Open the options at the codes, then the arming step; set it if given."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "codes"}
    )
    assert "code_arming" in result["menu_options"]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "code_arming"}
    )
    if value is not None:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_ARM_WITHOUT_CODE: value}
        )
        await hass.async_block_till_done()
    return result


async def test_arming_without_code(
    hass: HomeAssistant, fake_panel: FakePanel, setup: Setup
) -> None:
    """Arming needs no code; nobody is named as the one who armed."""
    await setup(code="4711", **ARM_FREELY)
    state = get_state(hass)
    assert state.attributes["code_arm_required"] is False
    # the keypad stays for disarming
    assert state.attributes["code_format"] == "number"
    await call_panel(hass, "alarm_arm_away", code=None)
    assert get_state(hass).state == AlarmControlPanelState.ARMED_AWAY
    assert get_state(hass).attributes["changed_by"] is None
    assert fake_panel.partitions[1].state == PartitionState.SET


async def test_arm_home_without_code(
    hass: HomeAssistant, fake_panel: FakePanel, setup: Setup
) -> None:
    """Arming internally needs no code either."""
    await setup(code="4711", **ARM_FREELY)
    await call_panel(hass, "alarm_arm_home", code=None)
    assert get_state(hass).state == AlarmControlPanelState.ARMED_HOME


@pytest.mark.parametrize("code", [None, "", "1234", "abcd"])
async def test_disarming_still_needs_the_code(
    hass: HomeAssistant, fake_panel: FakePanel, setup: Setup, code: str | None
) -> None:
    """Disarming without or with a wrong code sends nothing."""
    await setup(code="4711", **ARM_FREELY)
    await call_panel(hass, "alarm_arm_away", code=None)
    requests = list(fake_panel.stats.requests)
    with pytest.raises(ServiceValidationError):
        await call_panel(hass, "alarm_disarm", code=code)
    await hass.async_block_till_done()
    assert fake_panel.stats.requests == requests
    assert get_state(hass).state == AlarmControlPanelState.ARMED_AWAY
    assert fake_panel.partitions[1].state == PartitionState.SET


async def test_disarming_with_the_code(
    hass: HomeAssistant, fake_panel: FakePanel, setup: Setup
) -> None:
    """With the right code disarming works and names the user."""
    await setup(code="4711", **ARM_FREELY)
    await call_panel(hass, "alarm_arm_away", code=None)
    await call_panel(hass, "alarm_disarm", code="4711")
    assert get_state(hass).state == AlarmControlPanelState.DISARMED
    assert get_state(hass).attributes["changed_by"] == "Tester"


async def test_code_given_while_arming_is_checked(
    hass: HomeAssistant, fake_panel: FakePanel, setup: Setup
) -> None:
    """A wrong code is refused even for arming; the right one names the user."""
    await setup(code="4711", **ARM_FREELY)
    events = arming_failed_events(hass)
    with pytest.raises(ServiceValidationError):
        await call_panel(hass, "alarm_arm_away", code="1234")
    await hass.async_block_till_done()
    assert len(events) == 1
    assert fake_panel.stats.requests == ROUND
    assert get_state(hass).state == AlarmControlPanelState.DISARMED
    await call_panel(hass, "alarm_arm_away", code="4711")
    assert get_state(hass).attributes["changed_by"] == "Tester"


async def test_off_by_default(
    hass: HomeAssistant, fake_panel: FakePanel, setup: Setup
) -> None:
    """Without the option, arming needs the code as in the original."""
    await setup(code="4711")
    assert get_state(hass).attributes["code_arm_required"] is True
    with pytest.raises(ServiceValidationError):
        await call_panel(hass, "alarm_arm_away", code=None)
    assert fake_panel.stats.requests == ROUND


async def test_option_in_the_codes_menu(
    hass: HomeAssistant, fake_panel: FakePanel, setup: Setup
) -> None:
    """The option is switched in the options, without a reload."""
    entry = await setup(code="4711")
    result = await _code_arming(hass, entry)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "code_arming"
    result = await _code_arming(hass, entry, True)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ARM_WITHOUT_CODE] is True
    # the codes are kept
    assert entry.options["codes"]
    assert get_state(hass).attributes["code_arm_required"] is False
    await call_panel(hass, "alarm_arm_away", code=None)
    assert get_state(hass).state == AlarmControlPanelState.ARMED_AWAY
    await _code_arming(hass, entry, False)
    assert get_state(hass).attributes["code_arm_required"] is True


async def test_no_option_without_codes(
    hass: HomeAssistant, fake_panel: FakePanel, setup: Setup
) -> None:
    """Without codes nothing needs a code anyway; the option isn't offered."""
    entry = await setup()
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "codes"}
    )
    assert result["menu_options"] == ["add_code"]
