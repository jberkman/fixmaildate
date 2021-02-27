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
import os
import sys
import re
import logging


def fix_dir(dname):
    """ Parse the headers and fix the file stamp and name """
    for fname in os.listdir(dname):
        fname = os.path.join(dname, fname)
        file_path = open(fname, encoding="ISO-8859-1")
        msg = Parser().parse(file_path, True)
        if 'Date' in str(msg):
            date = parsedate_tz(str(msg['Date']))
            if date:
                try:
                    new_timestamp = mktime_tz(date)
                    old_timestamp = re.search(r'(?:cur\/)(\d+)', fname).group(1)
                    new_filename = fname.replace(old_timestamp, str(new_timestamp))

                    if str(new_timestamp) not in fname:
                        os.utime(fname, (new_timestamp, new_timestamp))
                        os.rename(fname, new_filename)
                except (ValueError, AttributeError):
                    logging.warning("Invalid date '%s' for %s: %s" % (msg['Date'], fname, date))
            else:
                logging.warning("Could not parse date '%s' for %s" % (msg['Date'], fname))
        else:
            logging.warning('No Date header in %s' % (fname))


def crawl_dir(dname):
    """ Recursively crawl the directory """
    try:
        for fname in os.listdir(dname):
            if fname == 'cur':
                try:
                    os.remove(os.path.join(dname, 'dovecot.index.cache'))
                except OSError as exc:
                    if exc.errno != 2:
                        raise
                fix_dir(os.path.join(dname, fname))
            else:
                crawl_dir(os.path.join(dname, fname))
    except OSError as exc:
        if exc.errno != 20 and exc.errno != 2:
            raise


def main(argv):
    """ Run the fixer """
    if len(argv) != 1:
        logging.error('Usage: fixmaildate.py <startdir>')
        sys.exit(1)
    crawl_dir(argv[0])


if __name__ == "__main__":
    main(sys.argv[1:])
