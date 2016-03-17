

# Introduction #

I'm a software engineer, so I know how an issue tracker can save you lots of time.  I even know that without one you can successfully keep track of so few things at once.  I knew that an issue tracker could be of great use even in my normal life, unrelated to programming.  It would let me organize my life.  It would even be useful to my wife, if it was simple to use.  I couldn't find anything user-friendly enough, so I started this project.

What differs it from other issue trackers:

  * It's simple.  It has very few features.  You can post/edit issues, comment on them, and use labels to organize them.  You don't care about milestones, OS versions or Q&A. However, if you ever used [Google Code's issue tracker](http://code.google.com/p/support/wiki/IssueTracker), you know that you can do a lot with labels.
  * It's easy to install.  You don't need a server.  You can host it at Google.  You can plug it in to your existing GAE project.  I'm also planning to add it to the [Google Apps Marketplace](https://www.google.com/enterprise/marketplace/?pli=1) later.

What differs it from todo lists, of which there are many:

  * You can comment on issues.  Imagine you want a new bed or a cell phone, and there's so much options available.  You need time find best options and choose one.  Try stuffing that in a todo list.


# Features #

  * Status tracking.  By default issues have the "Open" label, issues with the "Closed" label are hidden.
  * Custom list columns.  Labels with a dash are treated as "ColumnName-Value".  If a listed issue has such a label, a "ColumnName" column is added to the table, with value "Value" for that issue.  Such columns are sorted alphabetically.
  * [Markdown](http://daringfireball.net/projects/markdown/syntax) syntax.
  * [Gravatars](http://www.gravatar.com/).
  * The [Universal Edit Button](http://universaleditbutton.org/) is supported.


# Installation #

The tracker is a Python package, e.g. a directory full of files.  To install it, just copy that directory to your GAE application root folder, then add these lines to your app.yaml file:

```
handlers:
- url: /tracker
  script: gaetracker
  login: optional
- url: /gae-tracker/static/
  static_dir: gaetracker/static
```

This will install the tracker to your application at page `/tracker` (you can safely use anything else, even `/`).  If you want to disable anonymous access, change [the "login" property](http://code.google.com/appengine/docs/python/config/appconfig.html#Requiring_Login_or_Administrator_Status) to "always"; if you only want to let domain admins use the tracker, change login to "admin".

You will also need to add [this](http://gae-tracker.googlecode.com/hg/index.yaml) to your index.yaml and you're ready to go.


# Screenshots #

This is how you submit an issue:

![http://wiki.gae-tracker.googlecode.com/hg/images/gae-tracker-submit.png](http://wiki.gae-tracker.googlecode.com/hg/images/gae-tracker-submit.png)

There are some built-in defaults.

This is what an existing issue looks like:

![http://wiki.gae-tracker.googlecode.com/hg/images/gae-tracker-comments.png](http://wiki.gae-tracker.googlecode.com/hg/images/gae-tracker-comments.png)

You can see Gravatar in action, and the whole page is quite clean and simple.  Labels are shown in the upper right corner.

And this is the list of issues, also very simple:

![http://wiki.gae-tracker.googlecode.com/hg/images/gae-tracker-list.png](http://wiki.gae-tracker.googlecode.com/hg/images/gae-tracker-list.png)

That's all.


# Backing up #

To save all your data in JSON access the `?action=export` page.  If you want to save only certain issues, access the `?action=export&label=xyz` page.  A link to download listed issues is always shows below the issue list table.

To load your data back, use the `?action=import` page, a link to which is also always below the table.

You must be logged in for these functions to work.