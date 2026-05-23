from app.models import CheckSemanticCacheInput, CheckSemanticCacheOutput


def lookup(params: CheckSemanticCacheInput) -> CheckSemanticCacheOutput:
    return CheckSemanticCacheOutput(
        cache_hit=False,
        cached_report=None,
    )
