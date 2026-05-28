import traceback


def exception_format(e: BaseException) -> str:
    tb = traceback.extract_tb(e.__traceback__)
    last = tb[-1] if tb else None
    filename = last.filename if last else "?"
    line = last.lineno if last else "?"
    return (
        f"[{type(e).__name__}]\n"
        f"  file: {filename}\n"
        f"  line: {line}\n"
        f"  msg : {e}"
    )