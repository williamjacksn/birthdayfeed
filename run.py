import birthdayfeed.app
import notch
import signal
import sys

log = notch.make_log('birthdayfeed.run')

def handle_sigterm(_signal, _frame):
    sys.exit()


signal.signal(signal.SIGTERM, handle_sigterm)
birthdayfeed.app.main()
