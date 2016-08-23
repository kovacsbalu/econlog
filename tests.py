# -*- coding: utf8 -*-

import mock
import requests_mock
import datetime
from econlog import econlog


class TestLogEntry():

    def setup_method(self, method):
        content = (u"bejegyzesKartonInit(1,'2016.03.30.','4','15','6','Gyenge','Délnyugat (DNy)',"
                   u"'Gyengén felhős','Nincs csapadék', '','1','08:00','16:30','szerda',"
                   u"{napijelentes:false,napi_bejegyzes:false});")
        self.le = econlog.LogEntry(1, 1, content)
        self.le.parse_log_entry()

    def test_date(self):
        assert self.le.log_entry.date == "2016.03.30."

    def test_temp7(self):
        assert self.le.log_entry.temp7 == "4"

    def test_temp13(self):
        assert self.le.log_entry.temp13 == "15"

    def test_temp21(self):
        assert self.le.log_entry.temp21 == "6"

    def test_wind_power(self):
        assert self.le.log_entry.wind_power == "Gyenge"

    def test_wind_direction(self):
        assert self.le.log_entry.wind_direction == "Délnyugat (DNy)"

    def test_sky(self):
        assert self.le.log_entry.sky == "Gyengén felhős"

    def test_rainfall(self):
        assert self.le.log_entry.rainfall == "Nincs csapadék"

    def test_other_weather(self):
        assert self.le.log_entry.other_weather == ""

    def test_working(self):
        assert self.le.log_entry.working == "1"

    def test_worktime_from(self):
        assert self.le.log_entry.worktime_from == "08:00"

    def test_worktime_to(self):
        assert self.le.log_entry.worktime_to == "16:30"

    def test_day(self):
        assert self.le.log_entry.day == "szerda"


class TestLogEntryComment():

    def setup_method(self, method):
        content = (u"replaceTableContent('table_bejegyzesek','<tr class=\'r0\' unique=\'1\'>"
                   u"<td style=\'text-align:center;\'>1</td>"
                   u"<td style=\'text-align:center;\'>09:20</td>"
                   u"<td style=\'text-align:left;\'>John Doe</td>"
                   u"<td style=\'text-align:left;\'>napi jelentés</td>"
                   u"<td style=\'text-align:left;\'>Example text.</td>"
                   u"<td style=\'text-align:center;\'><i class=\'icon-edit\' title=\'online\'></i></td></tr>','')")
        self.le = econlog.LogEntry(1, 1, content)
        self.le.parse_comments()

    def test_time(self):
        assert self.le.comments[0].time == "09:20"

    def test_name(self):
        assert self.le.comments[0].name == "John Doe"

    def test_comment_type(self):
        assert self.le.comments[0].comment_type == "napi jelentés"

    def test_text(self):
        assert self.le.comments[0].text == "Example text."


class TestLogEntryFull():

    def setup_method(self, method):
        content = (u"bejegyzesKartonInit(1,'2016.03.30.','4','15','6','Gyenge','Délnyugat (DNy)',"
                   u"'Gyengén felhős','Nincs csapadék', '','1','08:00','16:30','szerda',"
                   u"{napijelentes:false,napi_bejegyzes:false});"
                   u"replaceTableContent('table_bejegyzesek','<tr class=\'r0\' unique=\'1\'>"
                   u"<td style=\'text-align:center;\'>1</td>"
                   u"<td style=\'text-align:center;\'>09:20</td>"
                   u"<td style=\'text-align:left;\'>John Doe</td>"
                   u"<td style=\'text-align:left;\'>napi jelentés</td>"
                   u"<td style=\'text-align:left;\'>Example text.</td>"
                   u"<td style=\'text-align:center;\'><i class=\'icon-edit\' title=\'online\'></i></td></tr>','')")
        self.le = econlog.LogEntry(1, 1, content)
        self.le.parse_comments()
        self.le.parse_log_entry()

    def test_str(self):
        assert "Dátum" in str(self.le)
        assert "John Doe" in str(self.le)


class TestEConLog():

    def setup_method(self, method):
        self.ecl = econlog.EConLog("user", "passwd")

    def test_parse_jquery(self):
        original_content = ("$('#enaploTree').html("
                            "'<ul class=\'fa_naplo keret\'><li class=\'r0 sajatakta\'></li></ul>');"
                            "gridTreeInit();naplofaBezar();$('').data('inited','1');unblockUI();")
        parsed_content = "<ul class='fa_naplo keret'><li class='r0 sajatakta'></li></ul>"
        assert self.ecl.parse_jquery_html(original_content) == parsed_content

    def test_get_xpath_attrib(self):
        content = "<p><div azon='123|456' tipus=1><b>x</b></div></p>"
        xp = '//div[@tipus="1"]'
        attr = "azon"
        assert self.ecl.get_xpath_attrib(content, xp, attr) == ["123|456"]

    def test_login(self):
        self.ecl._get_log_ids = mock.Mock()
        with requests_mock.mock() as m:
            m.post('https://gate.gov.hu/sso/ap/ApServlet',
                   text='<html><body>ok</body></html>')
            m.get('https://gate.gov.hu/sso/InterSiteTransfer')
            success = self.ecl.login()
        assert success
        assert self.ecl._get_log_ids.called

    def test_login_failed(self):
        self.ecl._get_log_ids = mock.Mock()
        with requests_mock.mock() as m:
            m.post('https://gate.gov.hu/sso/ap/ApServlet',
                   text='<div><span class="fielderror">login failed</span></div>')
            m.get('https://gate.gov.hu/sso/InterSiteTransfer')
            success = self.ecl.login()
        assert not success
        assert not self.ecl._get_log_ids.called

    def test_get_log_ids(self):
        with requests_mock.mock() as m:
            m.get('https://enaplo.e-epites.hu/enaplo/ajax?method=enaplok_adatok',
                  text="$('#enaploTree').html('<p><div azon='123|456' tipus=1><b>x</b></div></p>');")
            self.ecl._get_log_ids()
        assert self.ecl.files == {"123": ["456"]}

    def test_get_log_entry_on_date(self):
        econlog.LogEntry = mock.Mock()
        dd = datetime.date(1988, 02, 05)
        dd_srt = dd.strftime("%Y.%m.%d.")
        ecl = econlog.EConLog("user", "passwd")
        ecl.files = {"123": ["456"]}
        with requests_mock.mock() as m:
            m.get('https://enaplo.e-epites.hu/enaplo/ajax?method=bejegyzes_karton_load&datum=%s&aktaid=%s&naploid=%s' % (dd_srt, "123", "456"), text="log_data")
            log = ecl.get_log_entry_on_date(dd)
        assert log[0].parse_log_entry.called
        assert log[0].parse_comments.called
