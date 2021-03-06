# econlog - Electronic Construction Log

[![Build Status](https://travis-ci.org/kovacsbalu/econlog.svg?branch=master)](https://travis-ci.org/kovacsbalu/econlog)
[![Coverage Status](https://coveralls.io/repos/github/kovacsbalu/econlog/badge.svg?branch=master)](https://coveralls.io/github/kovacsbalu/econlog?branch=master)

Show electronic construction log entries.

```python
#!/usr/bin/python

import datetime
from econlog import econlog
from getpass import getpass

passwd = getpass('Password:')
ecl = econlog.EConLog("example_user", passwd)
if not ecl.login():
    exit(1)
for log in ecl.get_log_entry_on_date(datetime.date(2015, 12, 15)):
    print log
```

```
python example.py 
Password:
Dátum:    2015.12.15. - kedd
Hőfokok:  7ó:1C - 13ó:2C
Szél:     Gyenge - Délnyugat (DNy)
Időjárás: Derült égbolt, Nincs csapadék, 
Munka:    1, 08:00-16:30

09:20 John Doe napi jelentés
Example text.
```
