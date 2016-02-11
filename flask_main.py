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
    #the parts that you fill in the database are the things that youll use to find stuff

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
    #app.logger.debug("here is type of date " + str(type(date)))
    text = request.form["Memo"]
    AddNewDatedMemo(date, text, collection)
    flask.session['memos'] = get_memos(collection) #filling the session object with updated memos
    for memo in flask.session['memos']:
        app.logger.debug("Memo: " + str(memo))
    return flask.render_template('index.html') #redirecting to index.html



def AddNewDatedMemo(date, text, collection):
    arrow_date = arrow.get(date, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_date = arrow_date.isoformat()
    #print("HERE: " + storage_date)
    record = { "type": "dated_memo", 
           "date": storage_date, 
           "text": text
          }
    collection.insert(record)
    

@app.route("/_CancelMemo", methods =["POST"])
def cancelMemo():
    return flask.render_template('index.html') #redirecting to index.html
    


@app.route("/removeMemo")
def removeMemo():
    temp_selected = request.args.get('toRemove', 0, type=str)
    selected = temp_selected.split()
    #selected = list(temp_selected)
    removeSelectedMemos(selected, collection)
    return "nothing"

def removeSelectedMemos(selected, collection):
    print("HEREEE " + str(selected))
    
    for record in collection.find():
        if (str(record["_id"]) in selected):
            collection.remove(record)
            
      

@app.route("/updateAfterDelete")
def updatePageAfterDelete():
    flask.session['memos'] = get_memos(collection) #filling the session object with updated memos
    for memo in flask.session['memos']:
        app.logger.debug("Memo: " + str(memo))
    return flask.render_template('index.html') #redirecting to index.html



# We don't have an interface for creating memos yet
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

# NOT TESTED with this application; may need revision 
#@app.template_filter( 'fmtdate' )
# def format_arrow_date( date ):
#     try: 
#         normal = arrow.get( date )
#         return normal.to('local').format("ddd MM/DD/YYYY")
#     except:
#         return "(bad date)"

@app.template_filter( 'humanize' )
def humanize_arrow_date( date ):
    """
    Date is internal UTC ISO format string.
    Output should be "today", "yesterday", "in 5 days", etc.
    Arrow will try to humanize down to the minute, so we
    need to catch 'today' as a special case. 
    """
    now = arrow.utcnow().to('local').replace(hour=0)
    return RelativeDate(date, now)
    
    
def RelativeDate(date, now):
    try:
        #then = arrow.get(date).to('local') #user date
        then = arrow.get(date)
        print("here is the user date: " + str(then))
        #now = arrow.utcnow().to('local')
        print("here is the now date: " + str(now))
        if then.date() == now.date(): #for big dif in hours dont want in 18 hours
            human = "Today"
        elif then.date() == (now.replace(days=+1)).date():
            human = "Tomorrow" 
        elif then.date() == (now.replace(days=-1)).date():
            human = "Yesterday"
        else: 
            human = then.humanize(now)
            if human == "a day ago": #i added this
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
        #record['date'] = arrow.get(record['date']).isoformat() #THIS IS A STRING
        #print("here is type!!: " + str(type(record['date'])))
        print("here: " + str(record))
        record['_id'] = str(record['_id'])
        #del record['_id']
        records.append(record)
    records.sort(key=lambda r: r["date"])
    return records 


if __name__ == "__main__":
    # App is created above so that it will
    # exist whether this is 'main' or not
    # (e.g., if we are running in a CGI script)
    app.debug=CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    # We run on localhost only if debugging,
    # otherwise accessible to world
    """
    if CONFIG.DEBUG:
        # Reachable only from the same computer
        app.run(port=CONFIG.PORT)
    else:
        # Reachable from anywhere 
        app.run(port=CONFIG.PORT,host="0.0.0.0")
    """
    app.run(port=CONFIG.PORT,host="0.0.0.0")
    

    
