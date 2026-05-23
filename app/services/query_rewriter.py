import re

from app.models import QueryRewriterInput, QueryRewriterOutput

_TIMESTAMP_PATTERNS = re.compile(
    r"\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
    r"|"
    r"[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"
)

_PID_PATTERNS = re.compile(
    r"\[?(?:PID|pid|process)?[:\s]*\d{2,5}\]?"
)

_THREAD_PATTERNS = re.compile(
    r"\[?Thread[-\s]\d+\]?"
    r"|"
    r"\[0x[0-9a-fA-F]+\]"
)

_MEMORY_ADDRESS = re.compile(r"0x[0-9a-fA-F]{4,16}")

_FILE_LINE_REF = re.compile(r'File\s+"[^"]+"\s*,\s*line\s+\d+', re.IGNORECASE)

_LINE_NUMBERS = re.compile(r"(?m)^\s*\d+[.:)]\s*")

_EXCEPTION_PATTERNS = re.compile(
    r"((?:\w+\.)*[A-Z]\w+(?:Error|Exception|Fault|Warning|SyntaxError|"
    r"ValueError|TypeError|KeyError|IndexError|AttributeError|ImportError|"
    r"ModuleNotFoundError|RuntimeError|StopIteration|OSError|IOError|"
    r"ZeroDivisionError|AssertionError|RecursionError|NotImplementedError))"
)


def query_rewriter(params: QueryRewriterInput) -> QueryRewriterOutput:
    cleaned = params.raw_log_payload
    cleaned = _TIMESTAMP_PATTERNS.sub("", cleaned)
    cleaned = _PID_PATTERNS.sub("", cleaned)
    cleaned = _THREAD_PATTERNS.sub("", cleaned)
    cleaned = _MEMORY_ADDRESS.sub("", cleaned)
    cleaned = _FILE_LINE_REF.sub("", cleaned)
    cleaned = _LINE_NUMBERS.sub("", cleaned)
    cleaned = re.sub(r"\n\s*\n", "\n", cleaned)
    cleaned = cleaned.strip()

    match = _EXCEPTION_PATTERNS.search(params.raw_log_payload)
    exception_type = match.group(1) if match else ""

    return QueryRewriterOutput(
        normalized_signature=cleaned,
        extracted_exception_type=exception_type,
    )
