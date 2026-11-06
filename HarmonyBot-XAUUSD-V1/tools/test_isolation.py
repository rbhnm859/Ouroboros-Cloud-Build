"""Safety-focused tests of the isolation audit. No repository mutation."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from audit_isolation import allowed_path, project_refs_safe, BASE_SHA, V1_BRANCH

class TestIsolation(unittest.TestCase):
    def test_source_paths_allowed(self):
        self.assertTrue(allowed_path("HarmonyBot-XAUUSD-V1/src/Test.cs"))
        self.assertTrue(allowed_path("HarmonyBot-XAUUSD-V1/docs/ENGINEERING_PLAN.md"))
    def test_only_new_workflow_allowed(self):
        self.assertTrue(allowed_path(".github/workflows/harmonybot-xauusd-v1-domain.yml"))
        self.assertFalse(allowed_path(".github/workflows/harmonybot-v74-r18-semantic.yml"))
    def test_v74_core_protected(self):
        self.assertFalse(allowed_path("HarmonyBot-V71/src/HarmonyBotV71.cs"))
        self.assertFalse(allowed_path("HarmonyBot-V74/r18/feasibility_certificate.py"))
    def test_v74_data_protected(self):
        self.assertFalse(allowed_path("HarmonyBot-V73/V73_RESEARCH_CUSTODY.json"))
        self.assertFalse(allowed_path("HarmonyBot-V71/final/V71_PAYOFF_DISCOVERY_TERMINAL.json"))
    def test_sensitive_root_path_protected(self):
        self.assertFalse(allowed_path("README.md"))
        self.assertFalse(allowed_path(".gitignore"))
    def test_path_traversal_protected(self):
        self.assertFalse(allowed_path("HarmonyBot-XAUUSD-V1/../HarmonyBot-V74/r18/file.py"))
        self.assertFalse(allowed_path("/HarmonyBot-XAUUSD-V1/x"))
        self.assertFalse(allowed_path("HarmonyBot-XAUUSD-V1\\..\\V74"))
    def test_historical_base_and_new_branch_pinned(self):
        self.assertEqual(40, len(BASE_SHA))
        self.assertTrue(V1_BRANCH.startswith("feat/harmonybot-xauusd-core-v1"))
    def test_project_reference_must_stay_inside_v1(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            folder=root/"HarmonyBot-XAUUSD-V1"/"src"/"Bot"
            folder.mkdir(parents=True)
            (folder/"Bot.csproj").write_text(
                '<Project><ItemGroup><ProjectReference Include="../../../HarmonyBot-V71/HarmonyBotV71.csproj" /></ItemGroup></Project>')
            self.assertTrue(any("CROSS_PROJECT_REFERENCE" in x for x in project_refs_safe(root)))
    def test_own_project_reference_accepted(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            folder=root/"HarmonyBot-XAUUSD-V1"/"src"/"Bot"
            core=root/"HarmonyBot-XAUUSD-V1"/"src"/"Core"
            folder.mkdir(parents=True)
            core.mkdir()
            (core/"Core.csproj").write_text("<Project></Project>")
            (folder/"Bot.csproj").write_text(
                '<Project><ItemGroup><ProjectReference Include="../Core/Core.csproj" /></ItemGroup></Project>')
            self.assertEqual([], project_refs_safe(root))

if __name__ == "__main__":
    unittest.main()
