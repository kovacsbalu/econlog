#!/usr/bin/python
# -*- coding: utf8 -*-

import datetime
import json
import pushbullet
import sqlite3
from econlog import econlog


class LogDB(object):

    def __init__(self, db_filename):
        self.conn = sqlite3.connect(db_filename)
        self.conn.text_factory = str
        self.cur = self.conn.cursor()
        self.create_table()
        self.inserted_rowids = []

    def create_table(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS logs (time TEXT PRIMARY KEY, log_entry TEXT, comment TEXT)')

    def insert_log(self, date, log):
        for comm in log.comments:
            time = date.strftime("%Y-%m-%d ") + comm.time
            log_entry = json.dumps(log.log_entry._asdict())
            comment = json.dumps(comm._asdict())
            try:
                self.cur.execute("INSERT INTO logs VALUES (?, ?, ?)", (time, log_entry, comment))
                self.conn.commit()
                self.inserted_rowids.append(self.cur.lastrowid)
            except sqlite3.IntegrityError:
                pass

    def get_new_comments(self):
        comments = []
        for comment in db.select_inserted_rows():
            comm_dict = json.loads(comment[0])
            comm_out = unicode("\n{time} {name} {comment_type}\n"
                               "{text}\n")
            comments.append(comm_out.format(**comm_dict))
        return comments

    def select_inserted_rows(self):
        sql = "select comment from logs where rowid in ({seq})".format(seq=','.join(['?']*len(self.inserted_rowids)))
        self.cur.execute(sql, self.inserted_rowids)
        return self.cur.fetchall()

    def __del__(self):
        if self.conn:
            self.conn.close()


class PushEnaplo(object):

    def __init__(self, api_key, srv_dev_name, target_name):
        self.pb = pushbullet.PushBullet(api_key)
        self.srv = self.get_srv_device(srv_dev_name)
        self.target = self.find_device_by_name(target_name)

    def get_srv_device(self, srv_dev_name):
        dev = self.find_device_by_name(srv_dev_name)
        if dev:
            return dev
        print "Device not found. Creating ..."
        success, dev = self.pb.new_device(srv_dev_name)
        if success:
            return dev
        raise RuntimeError("Error while creating new device.")

    def find_device_by_name(self, name):
        for dev in self.pb.devices:
            if dev.nickname == name:
                return dev

    def send_log(self, date, log):
        self.pb.push_note(date, log, device=self.target)


if __name__ == "__main__":
    LOG_USER = ""
    LOG_PASSWD = ""
    DB_FILE = ""
    PB_API_KEY = ""
    PB_SEND_FROM = ""
    PB_SEND_TO = ""

    ecl = econlog.EConLog(LOG_USER, LOG_PASSWD)
    if not ecl.login():
        exit(1)
    now = datetime.datetime.now()
    log = ecl.get_log_entry_on_date(now)
    pe = PushEnaplo(PB_API_KEY, PB_SEND_FROM, PB_SEND_TO)
    db = LogDB(DB_FILE)
    db.insert_log(now, log)
    for comment in db.get_new_comments():
        pe.send_log(now.strftime("%Y.%m.%d."), comment)
