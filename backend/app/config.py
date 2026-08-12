import os

USER_AGENT = "MAGNETBot/1.0 (+https://github.com/magnet; growth-research; contact: demo@magnet.local)"


def live_sources_enabled() -> bool:
    """Live connectors (Reddit/HN public search) are opt-in and separate from
    the AI live/demo toggle -- MAGNET's zero-key default must not depend on
    network access at all."""
    return os.environ.get("MAGNET_LIVE_SOURCES") == "1"
