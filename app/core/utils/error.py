import traceback


def exception_format(e: BaseException, full: bool = False) -> str:
    if full:
        return "".join(traceback.format_exception(type(e), e, e.__traceback__))

    tb = traceback.extract_tb(e.__traceback__)
    last = tb[-1] if tb else None
    filename = last.filename if last else "?"
    line = last.lineno if last else "?"
    func = last.name if last else "?"
    code = last.line if last else ""
    msg = str(e) or "(no message)"

    return (
        f"[{type(e).__name__}] {msg}\n"
        f"  at {func} ({filename}:{line})\n"
        f"    {code}"
    )