# -*- coding: utf-8 -*-
import imaplib
import email
import time
import datetime
from robot import logging
from dateutil import parser
from robot import config
from robot.sdk.AbstractPlugin import AbstractPlugin


class Plugin(AbstractPlugin):

    SLUG = "email"

    def getSender(self, msg):
        """
            Returns the best-guess sender of an email.

            Arguments:
            msg -- the email whose sender is desired

            Returns:
            Sender of the sender.
        """
        fromstr = str(msg["From"])
        ls = fromstr.split(" ")
        if len(ls) == 2:
            fromname = email.header.decode_header(str(ls[0]).strip('"'))
            sender = fromname[0][0]
        elif len(ls) > 2:
            fromname = email.header.decode_header(
                str(fromstr[: fromstr.find("<")]).strip('"')
            )
            sender = fromname[0][0]
        else:
            sender = msg["From"]
        if isinstance(sender, bytes):
            try:
                return sender.decode("utf-8")
            except UnicodeDecodeError:
                return sender.decode("gbk")
        else:
            return sender

    def isSelfEmail(self, msg):
        """ Whether the email is sent by the user """
        fromstr = str(msg["From"])
        addr = (fromstr[fromstr.find("<") + 1 : fromstr.find(">")]).strip('"')
        address = config.get()[self.SLUG]["address"].strip()
        return addr == address

    def getSubject(self, msg):
        """
            Returns the title of an email

            Arguments:
            msg -- the email

            Returns:
            Title of the email.
        """
        subject = email.header.decode_header(msg["subject"])
        if isinstance(subject[0][0], bytes):
            try:
                sub = subject[0][0].decode("utf-8")
            except UnicodeDecodeError:
                sub = subject[0][0].decode("gbk")
        else:
            sub = subject[0][0]
        to_read = False
        if sub.strip() == "":
            return ""
        to_read = config.get("/email/read_email_title", True)
        if to_read:
            return "邮件标题为 %s" % sub
        return ""

    def isNewEmail(msg):
        """ Wether an email is a new email """
        date = str(msg["Date"])
        dtext = date.split(",")[1].split("+")[0].strip()
        dtime = time.strptime(dtext, "%d %b %Y %H:%M:%S")
        current = time.localtime()
        dt = datetime.datetime(*dtime[:6])
        cr = datetime.datetime(*current[:6])
        return (cr - dt).days == 0

    def getDate(self, email):
        return parser.parse(email.get("date"))

    def getMostRecentDate(self, emails):
        """
            Returns the most recent date of any email in the list provided.

            Arguments:
            emails -- a list of emails to check

            Returns:
            Date of the most recent email.
        """
        dates = [self.getDate(e) for e in emails]
        dates.sort(reverse=True)
        if dates:
            return dates[0]
        return None

    def fetchUnreadEmails(self, since=None, markRead=False, limit=None):
        """
            Fetches a list of unread email objects from a user's email inbox.

            Arguments:
            since -- if provided, no emails before this date will be returned
            markRead -- if True, marks all returned emails as read in target inbox

            Returns:
            A list of unread email objects.
        """
        logger = logging.getLogger(__name__)
        profile = config.get()
        conn = imaplib.IMAP4(
            profile[self.SLUG]["imap_server"], profile[self.SLUG]["imap_port"]
        )
        conn.debug = 0

        msgs = []
        try:
            conn.login(profile[self.SLUG]["address"], profile[self.SLUG]["password"])
            conn.select(readonly=(not markRead))
            (retcode, messages) = conn.search(None, "(UNSEEN)")
        except Exception:
            logger.warning("抱歉，您的邮箱账户验证失败了，请检查下配置")
            return None

        if retcode == "OK" and messages != [b""]:
            numUnread = len(messages[0].split(b" "))
            if limit and numUnread > limit:
                return numUnread

            for num in messages[0].split(b" "):
                # parse email RFC822 format
                ret, data = conn.fetch(num, "(RFC822)")
                if data is None:
                    continue
                msg = email.message_from_string(data[0][1].decode("utf-8"))

                if not since or self.getDate(msg) > since:
                    msgs.append(msg)

        conn.close()
        conn.logout()

        return msgs

    def handle(self, text, parsed):
        msgs = self.fetchUnreadEmails(limit=5)

        if msgs is None:
            self.say(u"抱歉，您的邮箱账户验证失败了", cache=True)
            return

        if isinstance(msgs, int):
            response = "您有 %d 封未读邮件" % msgs
            self.say(response, cache=True)
            return

        senders = [str(self.getSender(e)) for e in msgs]

        if not senders:
            self.say(u"您没有未读邮件，真棒！", cache=True)
        elif len(senders) == 1:
            self.say(u"您有来自 {} 的未读邮件。{}".format(senders[0], self.getSubject(msgs[0])))
        else:
            response = u"您有 %d 封未读邮件" % len(senders)
            unique_senders = list(set(senders))
            if len(unique_senders) > 1:
                unique_senders[-1] = ", " + unique_senders[-1]
                response += "。这些邮件的发件人包括："
                response += " 和 ".join(senders)
            else:
                response += "，邮件都来自 " + unique_senders[0]
            self.say(response)

    def isValid(self, text, parsed):
        return any(word in text for word in [u"邮箱", u"邮件"])
