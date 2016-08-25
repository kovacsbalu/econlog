# -*- coding: utf8 -*-

import collections
import re
import requests
import time
from lxml import html


class LogEntry(object):

    def __init__(self, file_id, log_id, content):
        self._log_entry_content = ""
        self._comments_content = ""
        self.log_entry = None
        self.comments = []
        self.file_id = file_id
        self.log_id = log_id
        self.parse_content(content)

    def __str__(self):
        log_out = ("Dátum:    {date} - {day}\n"
                   "Hőfokok:  7ó:{temp7}C - 13ó:{temp13}C\n"  # - 21ó:{temp21}C\n"
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
                comment_id = "%s|%s|%s" % (self.file_id, self.log_id, data[0])
                data[0] = comment_id
                self.comments.append(comment._make([dd.encode('utf-8') for dd in data[0:5]]))


class EConLog(object):
    GATE_BASE = "https://gate.gov.hu/"
    LOGIN_URL = GATE_BASE + "sso/ap/ApServlet?partnerid=oeny&target=enaplo_ugyfel_eles"
    REDIRECT_TO_URL = GATE_BASE + "sso/InterSiteTransfer?TARGET=enaplo_ugyfel_eles&PARTNER=oeny"
    ELOG_BASE = "https://enaplo.e-epites.hu/enaplo/"
    FILE_URL = ELOG_BASE + "ajax?method=enaplok_adatok&htmlid=%s"
    LOG_URL = ELOG_BASE + "ajax?method=get_naplo_items&parentid=enaploAktaFa&aktaid=%s&htmlid=%s"
    REGISTRY_URL = ELOG_BASE + "ajax?method=bejegyzes_karton_load&datum=%s&aktaid=%s&naploid=%s&htmlid=%s"

    def __init__(self, name, password=""):
        self.sess = requests.Session()
        self.name = name
        self.password = password
        self.files = {}

    def login(self):
        post_data = {"felhasznaloNev": self.name, "jelszo": self.password}
        login = self.sess.post(url=self.LOGIN_URL, data=post_data)
        login_info = html.fromstring(login.text)
        login_err = login_info.xpath('//span[@class="fielderror"]/text()')
        if login_err:
            print login_err[0].strip()
            return False
        self.sess.get(url=self.REDIRECT_TO_URL)
        self.session_id = self.sess.cookies.get('session_id')
        self._get_file_ids()
        self._get_log_ids()
        return True

    def _get_file_ids(self):
        resp = self.sess.get(url=self.FILE_URL % self.session_id)
        content = self.parse_jquery_html(resp.text)
        for file_id in self.get_xpath_attrib(content, './/div[@tipus="0"]', 'azon'):
            if file_id not in self.files:
                self.files[file_id] = []

    def _get_log_ids(self):
        for file_id in self.files:
            resp = self.sess.get(url=self.LOG_URL % (file_id, self.session_id))
            content = self.parse_ajax(resp.text, file_id)
            for _id in self.get_xpath_attrib(content, './/div[@tipus="1"]', 'azon'):
                _, log_id = _id.split("|")
                self.files[file_id].append(log_id)

    def get_log_entry_on_date(self, date):
        date_str = date.strftime("%Y.%m.%d.")
        logs = []
        for file_id in self.files:
            for log_id in self.files[file_id]:
                url = self.REGISTRY_URL % (date_str, file_id, log_id, self.session_id)
                resp = self.sess.get(url=url)
                log = LogEntry(file_id, log_id, resp.text)
                log.parse_log_entry()
                log.parse_comments()
                if log.comments:
                    logs.append(log)
        return logs

    @staticmethod
    def parse_jquery_html(content):
        found = re.search(r"html\('(.*?)'\);", content)
        return found.group(1).replace("\\", "")

    @staticmethod
    def parse_ajax(content, file_id):
        found = re.search(r"%s','(.*?)'\);" % file_id, content)
        return found.group(1).replace("\\", "")

    @staticmethod
    def get_xpath_attrib(content, xpath_expr, attr):
        res = []
        tree = html.fromstring(content)
        tags = tree.xpath(xpath_expr)
        for tag in tags:
            res.append(tag.attrib.get(attr))
        return res
