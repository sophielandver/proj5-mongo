"""
Flask web app connects to Mongo database.
Keep a simple list of dated memoranda.

Representation conventions for dates: 
   - We use Arrow objects when we want to manipulate dates, but for all
     storage in database, in session or g objects, or anything else that
     needs a text representation, we use ISO date strings.  These sort in the
     order as arrow date objects, and they are easy to convert to and from
     arrow date objects.  (For display on screen, we use the 'humanize' filter
     below.) A time zone offset will 
   - User input/output is in local (to the server) time.  
"""

import flask
from flask import render_template
from flask import request
from flask import url_for

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we may still need time
from dateutil import tz  # For interpreting local times

# Mongo database
from pymongo import MongoClient


###
# Globals
###
import CONFIG

app = flask.Flask(__name__)


try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.memos #memos is name of database that you created 
    collection = db.dated  #dated is name of collection. you are creating this collection right now

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)


import uuid
app.secret_key = str(uuid.uuid4())

###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
  app.logger.debug("Main page entry")
  flask.session['memos'] = get_memos(collection) #filling the session object
  for memo in flask.session['memos']:
      app.logger.debug("Memo: " + str(memo))
  return flask.render_template('index.html')


@app.route("/_AddMemo", methods =["POST"])
def addMemo():
    date = request.form["Date"]
    text = request.form["Memo"]
    AddNewDatedMemo(date, text, collection)
    flask.session['memos'] = get_memos(collection) #filling the session object with updated memos
    for memo in flask.session['memos']:
        app.logger.debug("Memo: " + str(memo))
    return flask.render_template('index.html') #redirecting to index.html
    

@app.route("/_CancelMemo", methods =["POST"])
def cancelMemo():
    return flask.render_template('index.html') #redirecting to index.html
    


@app.route("/removeMemo")
def removeMemo():
    temp_selected = request.args.get('toRemove', 0, type=str)
    selected = temp_selected.split()
    removeSelectedMemos(selected, collection)
    return "nothing"
            
      

@app.route("/updateAfterDelete")
def updatePageAfterDelete():
    flask.session['memos'] = get_memos(collection) #filling the session object with updated memos
    for memo in flask.session['memos']:
        app.logger.debug("Memo: " + str(memo))
    return flask.render_template('index.html') #redirecting to index.html


@app.route("/create")
def create():
    app.logger.debug("Create")
    return flask.render_template('create.html')


@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    return flask.render_template('page_not_found.html',
                                 badurl=request.base_url,
                                 linkback=url_for("index")), 404

#################
#
# Functions used within the templates
#
#################


@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Date is internal UTC ISO format string.
    Output should be "today", "yesterday", "in 5 days", etc.
    Arrow will try to humanize down to the minute, so we
    need to catch 'today' as a special case. 
    """
    now = arrow.utcnow().to('local').replace(hour=0) #change to midnight hour 00:00
    return RelativeDate(date, now)
    
    
def RelativeDate(date, now):
    """
    This function returns the relative date of date to now. 
    Arguments: 
        date: an ISO date string 
        now: an arrow time object
    Returns: the relative date that date is to now. 
    """
    try:
        then = arrow.get(date)
        if then.date() == now.date(): 
            human = "Today"
        elif then.date() == (now.replace(days=+1)).date():
            human = "Tomorrow" 
        elif then.date() == (now.replace(days=-1)).date():
            human = "Yesterday"
        else: 
            human = then.humanize(now)
            if human == "a day ago": 
                human = "Yesterday"
            if human == "in a day":
                human = "Tomorrow"
    except: 
        human = date
    return human


#############
#
# Functions available to the page code above
#
##############
def get_memos(collection):
    """
    Returns all memos in the database, in a form that
    can be inserted directly in the 'session' object.
    """
    records = [ ] #list of dictionaries {"type": "dated_memo", "date": 06/04/1995, "text":"Please clean the car"}
    for record in collection.find( { "type": "dated_memo" } ):
        record['_id'] = str(record['_id'])
        records.append(record)
    records.sort(key=lambda r: r["date"])
    return records


def AddNewDatedMemo(date, text, collection):
    """
    Adds a dated memo into the collection. 
    Arguments:
        date: a string of the the form "MM/DD/YYYY"
        text: a string 
        collection: the collection within the database to which we will 
                    add the memo. 
    Returns: nothing
    """
    arrow_date = arrow.get(date, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_date = arrow_date.isoformat()
    record = { "type": "dated_memo", 
           "date": storage_date, 
           "text": text
          }
    collection.insert(record) 

def removeSelectedMemos(selected, collection):
    """
    Removes a list of memos given by a list of object id's from the collection. 
    Arguments:
        selected: a string containing the object id's of the memo's we wish to remove 
                  from the collection. Each object id is separated by 1 space. 
        collection: the collection within the database from which we will remove the memos. 
    Returns: nothing
    """
    for record in collection.find():
        if (str(record["_id"]) in selected):
            collection.remove(record)


if __name__ == "__main__":
    # App is created above so that it will
    # exist whether this is 'main' or not
    # (e.g., if we are running in a CGI script)
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    # We run on localhost only if debugging,
    # otherwise accessible to world
    
    if CONFIG.DEBUG:
        # Reachable only from the same computer
        app.run(port=CONFIG.PORT)
    else:
        # Reachable from anywhere 
        app.run(port=CONFIG.PORT,host="0.0.0.0")
    
  
    

    
