# econlog - Electronic Construction Log

[![Build Status](https://travis-ci.org/kovacsbalu/econlog.svg?branch=master)](https://travis-ci.org/kovacsbalu/econlog)
[![Coverage Status](https://coveralls.io/repos/github/kovacsbalu/econlog/badge.svg?branch=master)](https://coveralls.io/github/kovacsbalu/econlog?branch=master)

Show electronic construction log entries.

```python
import datetime
from econlog import econlog
from getpass import getpass

passwd = getpass('Password:')
ecl = econlog.EConLog("example_user", passwd)
if not ecl.login():
    exit(1)
log = ecl.get_log_entry_on_date(datetime.date(2016, 4, 6))
print log
```

```
python example.py 
Password:
Dátum:    2016.04.06. - szerda
Hőfokok:  7ó:10C - 13ó:25C
Szél:     Gyenge - Délnyugat (DNy)
Időjárás: Derült égbolt, Nincs csapadék, 
Munka:    1, 08:00-16:30

09:20 John Doe napi jelentés
Example text.
```
