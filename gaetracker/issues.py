# encoding=utf-8

import datetime
import os

from django.utils import simplejson
from google.appengine.api import taskqueue
from google.appengine.api import users

import model


def get_issue_by_id(issue_id):
    """Loads or creates an issue."""
    if issue_id:
        issue = model.TrackerIssue.gql('WHERE id = :1', int(issue_id)).get()
        if issue is None:
            issue = model.TrackerIssue(id=int(issue_id))
    else:
        issue = model.TrackerIssue()
        last = model.TrackerIssue.all().order('-id').get()
        if last is None:
            issue.id = 1
        else:
            issue.id = last.id + 1
    return issue


def update(data):
    """Takes a dictionary of strings, parses and updates/creates the issue."""
    issue = get_issue_by_id(data.get('id', None))
    for k, v in data.items():
        if k in('id', 'comment_count'):
            v = int(v)
        if k in ('author', 'owner'):
            v = users.User(v)
        if k in ('date_created', 'date_updated'):
            v = datetime.datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        setattr(issue, k, v)

    if issue.id:
        issue.comment_count = model.TrackerIssueComment.gql('WHERE issue_id = :1', issue.id).count()

    issue.put()
    return issue


def import_all(data, delayed=True):
    path = os.environ['PATH_INFO']
    for item in data:
        if delayed:
            taskqueue.add(url=path, params={ 'action': 'import-one', 'data': simplejson.dumps(item) })
        else:
            update(item)
