# -*- coding: utf-8 -*-

from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@192.168.27.37/adsl2'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)


class LineHosts(db.Model):
    __tablename__ = 'linehosts'

    id = db.Column(db.Integer, primary_key=True)
    line = db.Column(db.NVARCHAR(20), unique=True, index=True)
    host = db.Column(db.NCHAR(6), unique=True, index=True)
    status = db.Column(db.NVARCHAR(20), index=True)
    adsl_ip = db.Column(db.NVARCHAR(20))
    last_update_time = db.Column(db.DATETIME)

    def __repr__(self):
        return '<LineHosts %r>' % self.host
