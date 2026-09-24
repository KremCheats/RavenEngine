#!/usr/bin/env python3
"""Static regression checks for Raven's generated UI/control wiring."""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
GENERATOR = ROOT / "write_tree.py"

with tempfile.TemporaryDirectory() as td:
    subprocess.run(["python3", str(GENERATOR)], cwd=td, check=True)
    menu = (Path(td) / "Src" / "Menu.mm").read_text()
    esp = (Path(td) / "Src" / "ESP.mm").read_text()
    aimbot = (Path(td) / "Src" / "Aimbot.mm").read_text()
    settings = (Path(td) / "Src" / "Settings.mm").read_text()

    required_menu_fragments = [
        "self.ball.hidden  = (RavenSettings::uiOpenButton == 2);",
        "RavenSettings::miscMenuOpacity / 100.0",
        "- (void)reloadActiveTab",
        "sub.frame = CGRectMake(14, 26, MAX(40, w - 28), 18);",
        "sub.frame = CGRectMake(MAX(14, w - 126), 2, 112, 24);",
        "RavenSettings::save();",
    ]
    for fragment in required_menu_fragments:
        assert fragment in menu, f"missing menu wiring: {fragment}"

    required_runtime_fragments = [
        "if (RavenSettings::espBox) [self drawBox:boxRect color:boxColor];",
        "RavenSettings::aimMaxDist > 0.0f",
    ]
    assert required_runtime_fragments[0] in esp, f"missing runtime wiring: {required_runtime_fragments[0]}"
    assert required_runtime_fragments[1] in aimbot, f"missing runtime wiring: {required_runtime_fragments[1]}"

    for name in ["aimPrediction", "espSkeleton", "visFovCircle", "wpnRapidFire", "miscBunnyHop"]:
        assert name in settings, f"missing persisted setting: {name}"

print("UI generation and control wiring checks passed")
