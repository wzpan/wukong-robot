# -*- coding: utf-8-*-
import imaplib
import email
import time
import datetime
import logging
from dateutil import parser

SLUG = "email"


# 字符编码转换方法
def my_unicode(s, encoding):
    if encoding:
        return unicode(s, encoding)
    else:
        return unicode(s)


def getSender(msg):
    """
        Returns the best-guess sender of an email.

        Arguments:
        msg -- the email whose sender is desired

        Returns:
        Sender of the sender.
    """
    fromstr = msg["From"]
    ls = fromstr.split(' ')
    if(len(ls) == 2):
        fromname = email.Header.decode_header((ls[0]).strip('\"'))
        sender = my_unicode(fromname[0][0], fromname[0][1])
    elif(len(ls) > 2):
        fromname = email.Header.decode_header((fromstr[:fromstr.find('<')])
                                              .strip('\"'))
        sender = my_unicode(fromname[0][0], fromname[0][1])
    else:
        sender = msg['From']
    return sender


def isSelfEmail(msg, profile):
    """ Whether the email is sent by the user """
    fromstr = msg["From"]
    addr = (fromstr[fromstr.find('<')+1:fromstr.find('>')]).strip('\"')
    address = profile[SLUG]['address'].strip()
    return addr == address


def getSubject(msg, profile):
    """
        Returns the title of an email

        Arguments:
        msg -- the email

        Returns:
        Title of the email.
    """
    subject = email.Header.decode_header(msg['subject'])
    sub = my_unicode(subject[0][0], subject[0][1])
    to_read = False
    if sub.strip() == '':
        return ''
    if 'read_email_title' in profile:
        to_read = profile['read_email_title']
    if '[echo]' in sub or '[control]' in sub:
        return sub
    if to_read:
        return '邮件标题为 %s' % sub
    return ''


def isNewEmail(msg):
    """ Wether an email is a new email """
    date = msg['Date']
    dtext = date.split(',')[1].split('+')[0].strip()
    dtime = time.strptime(dtext, '%d %b %Y %H:%M:%S')
    current = time.localtime()
    dt = datetime.datetime(*dtime[:6])
    cr = datetime.datetime(*current[:6])
    return (cr - dt).days == 0


def isEchoEmail(msg, profile):
    """ Whether an email is an Echo email"""
    subject = getSubject(msg, profile)
    if '[echo]' in subject:
        return True
    return False


def isControlEmail(msg, profile):
    """ Whether an email is a control email"""
    subject = getSubject(msg, profile)
    if '[control]' in subject and isSelfEmail(msg, profile):
        return True
    return False


def getDate(email):
    return parser.parse(email.get('date'))


def getMostRecentDate(emails):
    """
        Returns the most recent date of any email in the list provided.

        Arguments:
        emails -- a list of emails to check

        Returns:
        Date of the most recent email.
    """
    dates = [getDate(e) for e in emails]
    dates.sort(reverse=True)
    if dates:
        return dates[0]
    return None


def fetchUnreadEmails(profile, since=None, markRead=False, limit=None):
    """
        Fetches a list of unread email objects from a user's email inbox.

        Arguments:
        profile -- contains information related to the user (e.g., email
                   address)
        since -- if provided, no emails before this date will be returned
        markRead -- if True, marks all returned emails as read in target inbox

        Returns:
        A list of unread email objects.
    """
    logger = logging.getLogger(__name__)
    conn = imaplib.IMAP4(profile[SLUG]['imap_server'],
                         profile[SLUG]['imap_port'])
    conn.debug = 0

    msgs = []
    try:
        conn.login(profile[SLUG]['address'], profile[SLUG]['password'])
        conn.select(readonly=(not markRead))
        (retcode, messages) = conn.search(None, '(UNSEEN)')
    except Exception:
        logger.warning("抱歉，您的邮箱账户验证失败了，请检查下配置")
        return None

    if retcode == 'OK' and messages != ['']:
        numUnread = len(str(messages[0]).split(' '))
        if limit and numUnread > limit:
            return numUnread

        for num in messages[0].split(' '):
            # parse email RFC822 format
            ret, data = conn.fetch(num, '(RFC822)')
            if data is None:
                continue
            msg = email.message_from_string(data[0][1])

            if not since or getDate(msg) > since:
                msgs.append(msg)

            if isEchoEmail(msg, profile):
                conn.store(num, '+FLAGS', '\Seen')

    conn.close()
    conn.logout()

    return msgs


def handle(text, mic, profile, wxbot=None):
    """
        Responds to user-input, typically speech text, with a summary of
        the user's email inbox, reporting on the number of unread emails
        in the inbox, as well as their senders.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., email
                   address)
        wxBot -- wechat robot
    """
    msgs = fetchUnreadEmails(profile, limit=5)

    if msgs is None:
        mic.say(
            u"抱歉，您的邮箱账户验证失败了", cache=True)
        return

    if isinstance(msgs, int):
        response = "您有 %d 封未读邮件" % msgs
        mic.say(response, cache=True)
        return

    senders = [getSender(e) for e in msgs]

    if not senders:
        mic.say(u"您没有未读邮件，真棒！", cache=True)
    elif len(senders) == 1:
        mic.say(u"您有来自 " + senders[0] + " 的未读邮件")
    else:
        response = u"您有 %d 封未读邮件" % len(
            senders)
        unique_senders = list(set(senders))
        if len(unique_senders) > 1:
            unique_senders[-1] = ', ' + unique_senders[-1]
            response += "。这些邮件的发件人包括："
            response += ' 和 '.join(senders)
        else:
            response += "，邮件都来自 " + unique_senders[0]
        mic.say(response)


def isValid(text):
    """
        Returns True if the input is related to email.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return any(word in text for word in [u'邮箱', u'邮件'])
