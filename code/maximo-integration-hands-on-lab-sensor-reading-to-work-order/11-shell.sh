$ python consume.py demo-readers       # first time
[demo-readers] read 5 messages
$ python consume.py demo-readers       # same group again
[demo-readers] read 0 messages
$ python consume.py audit-team         # a different group
[audit-team] read 5 messages
