#!/usr/bin/python

import datetime
from econlog import econlog
from getpass import getpass

passwd = getpass('Password:')
ecl = econlog.EConLog("example_user", passwd)
if not ecl.login():
    exit(1)
log = ecl.get_log_entry_on_date(datetime.date(2016, 04, 06))
print log
