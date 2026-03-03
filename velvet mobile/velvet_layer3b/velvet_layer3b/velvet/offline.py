from typing import List, Tuple

def offline_fallback(user_text: str,
                     recent_context: List[Tuple[str, str]],
                     mode: str) -> str:
    ctx = ""
    if recent_context:
        ctx = f"I still have your last thread in memory: \"{recent_context[-1][1][:120]}\". "

    mode_hint = f"(Mode: {mode}) " if mode != "Normal" else ""

    return (
        f"{mode_hint}Network isn't reachable right now. "
        f"{ctx}"
        "You can rephrase, or tell me what you want to stage locally."
    )
