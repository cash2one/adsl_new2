# -*- coding:utf-8 -*-

from flask import Flask, request, make_response, jsonify, redirect, url_for, Response
from flask.ext.script import Manager, Shell
import sys, logging, datetime
from LineHosts import LineHosts
from LineHosts import db as db_linehosts

app = Flask(__name__)
manager = Manager(app)

TM_DELTA = 60 * 60 * 10
LB_IP = '183.61.80.68'
logger = logging.getLogger('access')


def getclientip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.headers:
        clientip = request.headers['HTTP_X_FORWARDED_FOR']
    else:
        clientip = request.remote_addr

    return clientip


@app.route('/')
def index():
    ip = getclientip(request)
    logger.debug(ip + ' ' + request.method + ' ' + request.full_path)

    return redirect(url_for('adsl_list'))


@app.route('/adsl/list')
def adsl_list():
    ip = getclientip(request)
    logger.info(ip + ' ' + request.method + ' ' + request.full_path)

    queries = LineHosts.query.filter_by(status=u'available').all()
    # queries = LineHosts.objects.filter(status='available')
    rets = ''
    if len(queries) > 0:
        for query in queries:
            # if query.status.strip() == 'available':
            if (query.last_update_time + datetime.timedelta(seconds=TM_DELTA)) > datetime.datetime.now():
                str = query.host + ' ' + query.line + ' ONLINE\n'
            else:
                str = query.host + ' ' + query.line + ' ERROR\n'

            rets += str

    return make_response(rets)


@app.route('/adsl/host/report', methods=['POST', ])
def adsl_host_report():
    ip = getclientip(request)
    logger.info(ip + ' ' + request.method + ' ' + request.full_path + ' ' + str(request.form))

    if request.headers.get('User-Agent').lower() == 'dj-adsl-backend':
        if 'ip' in request.form:
            ips = request.form['ip']
            for ip in ips.split(','):
                line = LineHosts.query.filter_by(line=ip).first()
                # line = LineHosts.objects.filter(host=ip)
                if line:
                    line.status = u'used'
                    print line.status
                    db_linehosts.session.add(line)
                    db_linehosts.session.commit()
                    # line[0].save()
            return make_response('OK')

        elif 'host' in request.form:
            host = request.form['host']
            ret = LineHosts.query.filter_by(host=host).first()
            # ret = LineHosts.objects.filter(host=host)
            if ret > 0:
                ret.adsl_ip = ip
                ret.last_update_time = datetime.datetime.now()
                ret.status = u'available'
                db_linehosts.session.add(ret)
                db_linehosts.session.commit()
                # ret[0].save()

                return make_response('OK')
            else:
                n = '8' + host.replace('seo', '')
                line = LB_IP + ':' + n
                record = LineHosts(host=host, line=line, adsl_ip=ip, status=u'available',
                                   last_update_time=datetime.datetime.now())
                db_linehosts.session.add(record)
                db_linehosts.session.commit()
                # record.save()

                return make_response('add new line, host:' + host + ' line:' + line)
        else:
            return 'NOOP', 400
    else:
        return 'NOT AUTHORIZED', 400


@app.route('/adsl/status', methods=['GET', "POST"])
def adsl_status():
    ip = getclientip(request)
    logger.info(ip + ' ' + request.method + ' ' + request.full_path)

    if request.method == 'GET':
        if 'show' in request.args:
            if request.args['show'] == 'all':
                rets = ''
                queries = LineHosts.query.all()
                # queries = LineHosts.objects.all()
                for query in queries:
                    td = (datetime.datetime.now() - query.last_update_time)
                    tmdelta = td.days * 3600 * 24 + td.seconds
                    if query.status == u'available' and tmdelta <= TM_DELTA:
                        s = query.host + ' ' + query.line + ' ' + query.adsl_ip + ' ' + query.status + ' ' + ' last updated before ' + str(
                            tmdelta) + ' seconds.'
                    elif tmdelta > TM_DELTA:
                        s = query.host + ' ' + query.line + ' ' + query.adsl_ip + ' ' + query.status + ' ' + ' last updated before ' + str(
                            tmdelta) + ' seconds. WARN_TTL1min'
                    else:
                        s = query.host + ' ' + query.line + ' ' + query.adsl_ip + ' ' + query.status + ' ' + ' last updated before ' + str(
                            tmdelta) + ' seconds. WARN_status'
                    rets += s + '\n'

                return make_response(rets)
            else:
                host = request.args['show']
                queries = LineHosts.query.filter_by(host=host)
                # queries = LineHosts.objects.filter(host=host)
                if len(queries) > 0:
                    return make_response(queries[0].status)
                else:
                    return make_response(404)
        else:
            rets = ''
            queries = LineHosts.query.filter_by(status=u'available').all()
            # queries = LineHosts.objects.all()
            for query in queries:
                tmdelta = (datetime.datetime.now() - query.last_update_time).seconds
                if tmdelta <= TM_DELTA:
                    s = query.host + ' ' + query.line + ' ' + query.adsl_ip + ' ' + query.status + ' ' + ' last updated before ' + str(
                        tmdelta) + ' seconds.'

                    rets += s + '\n'

            return make_response(rets)
    else:
        return make_response(400)


def make_shell_context():
    return dict(app=app,db=db_linehosts,LineHosts=LineHosts)

if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    app.run(host=host, port=port, debug=True)
    # manager.add_command('shell', Shell(make_context=make_shell_context))
    # manager.run()
