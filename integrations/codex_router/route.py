"""Deterministic, advisory task routing. It cannot start Codex or grant permissions."""
from dataclasses import dataclass
from hashlib import sha256
import json
import re

CONTROL = ("部署", "上線", "正式合併", "merge to", "force push", "實盤", "下單", "密鑰", "金鑰", "api key", "交易帳戶", "付費", "計費")
CODE = ("修復", "debug", "寫程式", "修改程式", "重構", "refactor", "編譯", "compile", "build", "codex", "修改代碼", "實作", "implementation", "修正 bug")
VALIDATION = ("驗收", "稽核", "validate", "validation", "review pr", "安全審查", "獨立審查")
QUANT = ("勝率", "回測績效", "first-passage", "oof", "out-of-sample", "量化", "統計", "風險報酬", "pf_r", "meanr")
AUDIT = ("github", "ci", "workflow", "pull request", "actions", "sha", "日誌", "logs", "狀態")

@dataclass(frozen=True)
class RouteDecision:
    primary: str
    specialists: tuple[str, ...]
    controlled: bool
    codex_candidate: bool
    dispatchable: bool = False

def classify(text: str) -> RouteDecision:
    q = text.casefold()
    has = lambda words: any(w.casefold() in q for w in words)
    controlled, code = has(CONTROL), has(CODE)
    if controlled:
        route, skills = "CONTROLLED_CHANGE", ("Director", "Engineer", "Validation")
    elif code:
        route, skills = "CODE_TASK", ("Director", "Engineer", "Validation")
    elif has(VALIDATION):
        route, skills = "VALIDATION", ("Validation",)
    elif has(QUANT):
        route, skills = "QUANT", ("Quant", "Validation")
    elif has(AUDIT):
        route, skills = "GITHUB_AUDIT", ("Director", "Engineer")
    else:
        route, skills = "RESEARCH", ("Director",)
    return RouteDecision(route, skills, controlled, code, False)

def task_key(repo: str, branch: str, base_sha: str, objective: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{40}", base_sha.lower()):
        raise ValueError("Exact 40-character Git SHA required")
    normalized = re.sub(r"\s+", " ", objective.strip().casefold())
    payload = json.dumps([repo.strip().lower(), branch.strip(), base_sha.lower(), normalized], ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()
