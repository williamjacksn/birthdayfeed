import birthdayfeed.app
import notch
import signal
import sys

notch.configure()


def handle_sigterm(_signal, _frame):
    sys.exit()


signal.signal(signal.SIGTERM, handle_sigterm)
birthdayfeed.app.main()
