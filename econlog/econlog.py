# -*- coding: utf8 -*-

import collections
import re
import requests
import time
from lxml import html


class LogEntry(object):

    def __init__(self, content):
        self._log_entry_content = ""
        self._comments_content = ""
        self.log_entry = None
        self.comments = []
        self.parse_content(content)

    def __str__(self):
        log_out = ("Dátum:    {date} - {day}\n"
                   "Hőfokok:  7ó:{temp7}C - 13ó:{temp13}C"  # - 21ó:{temp21}C\n"
                   "Szél:     {wind_power} - {wind_direction}\n"
                   "Időjárás: {sky}, {rainfall}, {other_weather}\n"
                   "Munka:    {working}, {worktime_from}-{worktime_to}\n")
        comm_out = ("\n{time} {name} {comment_type}\n"
                    "{text}\n")
        out = log_out.format(**self.log_entry._asdict())
        for comment in self.comments:
            out += comm_out.format(**comment._asdict())
        return out

    def parse_content(self, content):
        for cont in content.split(");"):
            if cont.startswith("bejegyzesKartonInit("):
                self._log_entry_content = re.findall(r"'(.*?)',", cont)
            if cont.startswith("replaceTableContent('table_bejegyzesek'"):
                self._comments_content = re.findall(r"'(.*?)',", cont)

    def parse_log_entry(self):
        # function bejegyzesKartonInit(
        # mentett, datum, hofok7, hofok13, hofok21, szelero, szelirany, egkep, csapadek,
        # egyebidojaras, munkavegzes, munkaido_tol, munkaido_ig, hetnap, isfuncarr)
        # bejegyzesKartonInit(1,'2016.03.30.','4','15','','Gyenge','Délnyugat (DNy)','Gyengén felhős','Nincs csapadék',
        # '','0','','','szerda',{napijelentes:false,napi_bejegyzes:false});
        fields = ('date', 'temp7', 'temp13', 'temp21', 'wind_power', 'wind_direction', 'sky', 'rainfall',
                  'other_weather', 'working', 'worktime_from', 'worktime_to', 'day')
        log = collections.namedtuple('LogEntry', ' '.join(fields))
        self.log_entry = log._make([rc.encode('utf-8') for rc in self._log_entry_content[0:13]])

    def parse_comments(self):
        # replaceTableContent('table_bejegyzesek','<tr class=\'r0\' unique=\'1\'>
        # <td style=\'text-align:center;\'>1</td>
        # <td style=\'text-align:center;\'>09:20</td>
        # <td style=\'text-align:left;\'>John Doe</td><td style=\'text-align:left;\'>napi jelentés</td>
        # <td style=\'text-align:left;\'>Example text.</td>
        # <td style=\'text-align:center;\'><i class=\'icon-edit\' title=\'online\'></i></td></tr>')
        fields = ('id', 'time', 'name', 'comment_type', 'text')
        comment = collections.namedtuple('Comment', ' '.join(fields))
        data = self._comments_content[1]
        tree = html.fromstring(self._comments_content[1])
        rows = tree.xpath('//tr')
        for row in rows:
            data = row.xpath("td/text()")
            if len(data) >= 5:
                self.comments.append(comment._make([dd.encode('utf-8') for dd in data[0:5]]))


class EConLog(object):
    GATE_BASE = "https://gate.gov.hu/"
    LOGIN_URL = GATE_BASE + "sso/ap/ApServlet?partnerid=oeny&target=enaplo_ugyfel_eles"
    REDIRECT_TO_URL = GATE_BASE + "sso/InterSiteTransfer?TARGET=enaplo_ugyfel_eles&PARTNER=oeny"
    ELOG_BASE = "https://enaplo.e-epites.hu/enaplo/"
    LOG_URL = ELOG_BASE + "ajax?method=enaplok_adatok&htmlid=&_=%d"
    REGISTRY_URL = ELOG_BASE + "ajax?method=bejegyzes_karton_load&datum=%s&aktaid=%s&naploid=%s&htmlid=%s&_=1459619768561"

    def __init__(self, name, password=""):
        self.sess = requests.Session()
        self.name = name
        self.password = password
        self.file_id = None
        self.log_id = None

    def login(self):
        post_data = {"felhasznaloNev": self.name, "jelszo": self.password}
        login = self.sess.post(url=self.LOGIN_URL, data=post_data)
        login_info = html.fromstring(login.text)
        login_err = login_info.xpath('//span[@class="fielderror"]/text()')
        if login_err:
            print login_err[0].strip()
            return False
        self.sess.get(url=self.REDIRECT_TO_URL)
        self._get_log_ids()
        return True

    def _get_log_ids(self):
        resp = self.sess.get(url=self.LOG_URL % time.time())
        content = self.parse_jquery_html(resp.text)
        ids = self.get_xpath_attrib(content, '//div[@class="naploelem sajat"]', 'azon')
        self.file_id, self.log_id = ids.split("|")

    def get_log_entry_on_date(self, date):
        date_str = date.strftime("%Y.%m.%d.")
        url = self.REGISTRY_URL % (date_str, self.file_id, self.log_id, self.sess.cookies.get('session_id'))
        resp = self.sess.get(url=url)
        log = LogEntry(resp.text)
        log.parse_log_entry()
        log.parse_comments()
        return log

    @staticmethod
    def parse_jquery_html(content):
        found = re.search(r"html\('(.*?)'\);", content)
        return found.group(1).replace("\\", "")

    @staticmethod
    def get_xpath_attrib(content, xpath_expr, attr):
        tree = html.fromstring(content)
        tags = tree.xpath(xpath_expr)
        return tags[0].attrib.get(attr)
