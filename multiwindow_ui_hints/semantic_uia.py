"""Semantic UIA scan: IUIAutomationElement.FindAll with OrCondition over control types.

Avoids walking the full tree with descendants(); the provider filters by control type + enabled.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

# Pywinauto `element_info.control_type` short names -> uiautomation.ControlType attribute names.
_PYWINAUTO_TO_CONTROL_TYPE_ATTR: dict[str, str] = {
    "Button": "ButtonControl",
    "Hyperlink": "HyperlinkControl",
    "Edit": "EditControl",
    "ComboBox": "ComboBoxControl",
    "CheckBox": "CheckBoxControl",
    "RadioButton": "RadioButtonControl",
    "ListItem": "ListItemControl",
    "MenuItem": "MenuItemControl",
    "TabItem": "TabItemControl",
    "TreeItem": "TreeItemControl",
    "DataItem": "DataItemControl",
}


def _control_type_ids(uia_module: Any, control_types: frozenset) -> List[int]:
    ct = uia_module.ControlType
    ids: List[int] = []
    for t in control_types:
        attr = _PYWINAUTO_TO_CONTROL_TYPE_ATTR.get(t)
        if attr:
            ids.append(int(getattr(ct, attr)))
    return sorted(set(ids))


def _fold_or_conditions(ia: Any, conds: List[Any]) -> Any:
    if not conds:
        raise ValueError("empty condition list")
    if len(conds) == 1:
        return conds[0]
    acc = conds[0]
    for c in conds[1:]:
        acc = ia.CreateOrCondition(acc, c)
    return acc


def _build_match_condition(ia: Any, uia_module: Any, control_types: frozenset) -> Any:
    prop = uia_module.PropertyId
    type_ids = _control_type_ids(uia_module, control_types)
    if not type_ids:
        raise ValueError("no control types mapped for semantic scan")
    type_conds = [ia.CreatePropertyCondition(prop.ControlTypeProperty, tid) for tid in type_ids]
    or_cond = _fold_or_conditions(ia, type_conds)
    enabled_cond = ia.CreatePropertyCondition(prop.IsEnabledProperty, True)
    return ia.CreateAndCondition(or_cond, enabled_cond)


def scan_interactive_descendants_semantic(
    hwnd: int,
    vx1: int,
    vy1: int,
    vx2: int,
    vy2: int,
    control_types: frozenset,
) -> Optional[List[Tuple[int, int, str, Any, Any]]]:
    """Return (top, left, name, uia_control, rect) tuples, or None if semantic scan cannot run."""
    if not hwnd:
        return None
    try:
        import uiautomation.uiautomation as uia
    except Exception:
        return None

    try:
        client = uia._AutomationClient.instance()
        ia = client.IUIAutomation
        core = client.UIAutomationCore
        tree_scope = core.TreeScope_Descendants
        cond = _build_match_condition(ia, uia, control_types)
        root_ctrl = uia.ControlFromHandle(hwnd)
        if root_ctrl is None:
            return None
        arr = root_ctrl.Element.FindAll(tree_scope, cond)
        if arr is None:
            return []
        n = int(arr.Length)
        out: List[Tuple[int, int, str, Any, Any]] = []
        for i in range(n):
            try:
                ele = arr.GetElement(i)
                ctrl = uia.Control.CreateControlFromElement(ele)
                if ctrl is None:
                    continue
                if ctrl.IsOffscreen:
                    continue
                rect = ctrl.BoundingRectangle
                if rect.width() < 8 or rect.height() < 8:
                    continue
                if rect.right < vx1 or rect.left > vx2 or rect.bottom < vy1 or rect.top > vy2:
                    continue
                name = ctrl.Name or ""
                out.append((rect.top, rect.left, name, ctrl, rect))
            except Exception:
                continue
        return out
    except Exception:
        return None
