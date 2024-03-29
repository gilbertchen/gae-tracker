# encoding=utf-8

import logging
import os
import re

from google.appengine.dist import use_library
use_library('django', '0.96')

from django.utils import simplejson
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import issues
import model

DEFAULT_ACTION = 'table'


def parse_labels(labels):
    labels = list(set(re.split('[, ]+', labels)))
    return sorted([l for l in labels if l])


class Action:
    def __init__(self, rh):
        self.rh = rh

    def render(self, data):
        self.rh.render(self.template, data)


class SubmitAction(Action):
    template = 'submit.tpl'

    def get(self):
        issue = self.get_issue()
        if self.rh.request.get('labels'):
            issue.labels.append(self.rh.request.get('labels'))
        self.render({
            'issue': issue,
        })

    def post(self):
        data = dict([(x, self.rh.request.get(x)) for x in self.rh.request.arguments()])
        if 'labels' in data:
            data['labels'] = parse_labels(data['labels'])
        if not data.get('id'):
            user = users.get_current_user()
            if user:
                data['author'] = user.email()
        issue = issues.update(data)
        self.rh.redirect(self.rh.request.path + '?action=' + DEFAULT_ACTION)
        #self.rh.redirect(self.rh.request.path + '?action=view&id=' + str(issue.id))

    def get_issue(self):
        issue = model.TrackerIssue()
        issue.labels = [ 'Open' ]
        user = users.get_current_user()
        if user is not None:
            issue.author = user
            issue.owner = user
        return issue


class EditAction(SubmitAction):
    template = 'edit.tpl'

    def get_issue(self):
        issue_id = int(self.rh.request.get('id'))
        issue = model.TrackerIssue.gql('WHERE id = :1', issue_id).get()
        if issue is None:
            raise Exception('Issue %u does not exist.' % issue_id)
        return issue


class ViewAction(Action):
    template = 'view.tpl'

    def get(self):
        issue_id = int(self.rh.request.get('id'))
        issue = issues.get_issue_by_id(issue_id)
        self.render({
            'issue': issue,
            'labels': sorted(issue.labels, key=lambda l: ('-' not in l, l.lower())),
            'resolved': 'Closed' in issue.labels,
            'comments': model.TrackerIssueComment.gql('WHERE issue_id = :1 ORDER BY date_created', issue_id).fetch(100),
        })


class CommentAction(Action):
    def post(self):
        labels = parse_labels(self.rh.request.get('labels'))

        for l in ('Open', 'Closed'):
            if l in labels:
                labels.remove(l)

        if self.rh.request.get('resolved'):
            labels.append('Closed')
        else:
            labels.append('Open')

        issue_id = int(self.rh.request.get('id', '0'))
        issues.add_comment(issue_id, users.get_current_user(), self.rh.request.get('text'), labels=labels)
        self.rh.redirect(self.rh.request.path + '?action=view&id=' + str(issue_id))


class ListAction(Action):
    template = 'list.tpl'

    def get(self):
        label = self.rh.request.get('label')
        issues_ = issues.find_issues(label, closed=self.rh.request.get('closed'))

        self.render({
            'issues': issues_,
            'filter': label,
            'columns': self.get_columns(issues_),
        })

    def get_columns(self, issues):
        columns = []
        for issue in issues:
            for label in issue.labels:
                if '-' in label:
                    k, v = label.split('-', 1)
                    if k not in columns:
                        columns.append(k)
        return sorted(columns)


class TableAction(ListAction):
    template = 'table.tpl'

    def get(self):
        label = self.rh.request.get('label')
        issues_ = sorted(issues.find_issues(label, closed=self.rh.request.get('closed')), key=lambda i: i.summary.lower())

        data = [
            { 'pri': '1', 'title': u'Важно и срочно', 'issues': [] },
            { 'pri': '2', 'title': u'Важно, не срочно', 'issues': [] },
            { 'pri': '3', 'title': u'Срочно, не важно', 'issues': [] },
            { 'pri': '4', 'title': u'Ни срочно, ни важно', 'issues': [] },
        ]
        for issue in issues_:
            pri = [int(l[4:]) for l in issue.labels if l.lower().startswith('pri-')][0]
            if pri >= 1 and pri <= 4:
                data[pri-1]['issues'].append(issue)

        self.render({
            'filter': label,
            'data': data,
        })


class ExportAction(Action):
    def get(self):
        data = issues.export_json(self.rh.request.get('label') or None)
        self.rh.reply(data)


class ImportAction(Action):
    template = 'import.tpl'

    def get(self):
        self.render({ })

    def post(self):
        data = simplejson.loads(self.rh.request.get('dump'))
        issues.import_all(data)
        self.rh.redirect(self.rh.request.path)


class ImportOneAction(Action):
    def post(self):
        issue = issues.update(simplejson.loads(self.rh.request.get('data')), create=True)
        logging.info('Issue %u imported.' % issue.id)


class FixPriorityAction(Action):
    def get(self):
        for issue in issues.find_issues():
            labels = list(issue.labels)
            issues.fix_priority_labels(issue)
            if labels != issue.labels:
                issue.put()


class Tracker(webapp.RequestHandler):
    handlers = {
        'comment': CommentAction,
        'edit': EditAction,
        'export': ExportAction,
        'fixpriority': FixPriorityAction,
        'import': ImportAction,
        'import-one': ImportOneAction,
        'list': ListAction,
        'submit': SubmitAction,
        'table': TableAction,
        'view': ViewAction,
    }

    def get(self):
        self.call('get')

    def post(self):
        self.call('post')

    def call(self, method):
        action = self.request.get('action', DEFAULT_ACTION)
        if action in self.handlers:
            getattr(self.handlers[action](self), method)()
        else:
            self.reply('Don\'t know how to handle action "%s".' % action)

    def render(self, template_name, data, content_type='text/html'):
        data['path'] = self.request.path
        data['user'] = users.get_current_user()
        # logging.debug(u'Data for %s: %s' % (template_name, data))
        filename = os.path.join(os.path.dirname(__file__), 'templates', template_name)
        self.reply(template.render(filename, data), content_type=content_type)

    def reply(self, content, content_type='text/plain', status=200):
        self.response.headers['Content-Type'] = content_type + '; charset=utf-8'
        self.response.out.write(content)

handlers = [
    ('.*', Tracker),
]
