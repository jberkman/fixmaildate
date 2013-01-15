#!/bin/env python
'''
Copyright © 2013 Jacob Berkman <jacob@87k.net>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


I migrated from GMail to Mac OS X Server mail and the dates for
mails were all wrong in Mail.app (or, as the kids say, 'Apple
Mail'). I finally got tired of it and after a little research found
that this is determined by the mtime of the files in dovecot's
maildir, or mdir, or whatever it's called.

I wasn't the only one:
http://www.dovecot.org/list/dovecot/2008-July/032152.html

So I wrote this script.

It parses each file in a mail directory and then sets the mtime to
that date. I had 45000 mails and it worked pretty well, but I suggest
you stop your mail server while doing this. It recursively enters
directories so you can point it at a specific folder, user, or the
mail directory for all users.

After starting the server and reconnecting Mail.app, select each
folder and go to Mailbox -> Rebuild. It will download each message
again, so make sure you're on a fast connection to your server. Or
you could just recreate your account. Maybe there's a better way.
'''

from email.parser import Parser
from email.utils import parsedate_tz, mktime_tz
from datetime import datetime
import os, sys

def fixDir(dname):
    for fname in os.listdir(dname):
        fname = os.path.join(dname, fname)
        fp = open(fname)
        msg = Parser().parse(fp, True)
        if 'Date' in msg:
            date = parsedate_tz(msg['Date'])
            if date:
                # Ok I had some old emails with messed up Date headers as so:
                # Date: Sun, 22 Aug US/E 13:01:00 -0400
                # I knew these were briefly from '99-'00 so I manually fix that here.
                '''
                if date[0] < 1900:
                    if date[1] < 3:
                        year = 2000
                    else:
                        year = 1999
                    date = (year,) + date[1:]
                    print >> sys.stderr, "Fixing up year '%s' => '%s' for %s" % (msg['Date'], date, fname)
                '''
                try:
                    timestamp = mktime_tz(date)
                    os.utime(fname, (timestamp, timestamp))
                except ValueError:
                    print >> sys.stderr, "Invalid date '%s' for %s: %s" % (msg['Date'], fname, date)
            else:
                print >> sys.stderr, "Could not parse date '%s' for %s" % (msg['Date'], fname)
        else:
            print >> sys.stderr, 'No Date header in %s' % (fname)

def crawlDir(dname):
    try:
        for fname in os.listdir(dname):
            if fname == 'cur':
                try:
                    os.remove(os.path.join(dname, 'dovecot.index.cache'))
                except OSError as e:
                    if e.errno != 2:
                        raise
                fixDir(os.path.join(dname, fname))
            else:
                crawlDir(os.path.join(dname, fname))
    except OSError as e:
        if e.errno != 20 and e.errno != 2:
            raise

def main(argv):
    if len(argv) != 1:
        print 'Usage: fixmaildate.py <startdir>'
        sys.exit(1)
    crawlDir(argv[0])

if __name__ == "__main__":
    main(sys.argv[1:])
