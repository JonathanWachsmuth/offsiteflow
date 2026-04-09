# pipeline/cli.py
# ─────────────────────────────────────────────────────────────
# CLI entry point for the OffsiteFlow pipeline.
# All test data lives here — pipeline/run.py stays clean.
#
# Usage:
#   python3 -m pipeline.cli                          # interactive, dry run
#   python3 -m pipeline.cli --send                   # send real emails
#   python3 -m pipeline.cli --send --override-to me@example.com
#   python3 -m pipeline.cli --no-interactive         # skip approval step
#   python3 -m pipeline.cli --real-responses         # use live DB replies
# ─────────────────────────────────────────────────────────────

import argparse
import logging

from pipeline.run import run
from tests.fixtures.test_briefs import BRIEF_TEXT_LONDON
from tests.fixtures.synthetic_responses import SYNTHETIC_RESPONSES


def main():
    parser = argparse.ArgumentParser(description="OffsiteFlow pipeline runner")

    parser.add_argument(
        "--send", action="store_true", default=False,
        help="Send real emails (default: dry run)"
    )
    parser.add_argument(
        "--real-responses", action="store_true", default=False,
        help="Use real vendor responses from DB (default: synthetic)"
    )
    parser.add_argument(
        "--override-to", type=str, default=None,
        help="Redirect all outbound emails to this address"
    )
    parser.add_argument(
        "--save", action="store_true", default=False,
        help="Save shortlist to database"
    )
    parser.add_argument(
        "--no-interactive", action="store_true", default=False,
        help="Skip candidate approval step"
    )
    parser.add_argument(
        "--brief", type=str, default=None,
        help="Free-text event brief (overrides default test brief)"
    )
    parser.add_argument(
        "--log-level", type=str, default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: WARNING)"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    brief_input = args.brief or BRIEF_TEXT_LONDON

    run(
        brief_input          = brief_input,
        dry_run              = not args.send,
        synthetic            = not args.real_responses,
        synthetic_responses  = SYNTHETIC_RESPONSES,
        override_to          = args.override_to,
        save_to_db           = args.save,
        interactive          = not args.no_interactive
    )


if __name__ == "__main__":
    main()
