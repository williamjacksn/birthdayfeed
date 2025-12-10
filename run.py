import signal
import sys
import types

import notch

import birthdayfeed.app

notch.configure()


def handle_sigterm(_signal: int, _frame: types.FrameType | None) -> None:
    sys.exit()


signal.signal(signal.SIGTERM, handle_sigterm)
birthdayfeed.app.main()
