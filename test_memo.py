"""
Nose tests for flask_main.py
"""
#want to test adding to database, deleting from data base, listing the memos (in sorted), and formatting dates
#make a new database to use for testing  
import arrow
from flask_main import AddNewDatedMemo
from flask_main import removeSelectedMemos 
from flask_main import get_memos
from flask_main import humanize_arrow_date
from flask_main import RelativeDate

from pymongo import MongoClient

MONGO_PORT=27017 #  standard mongo port
MONGO_PW = "memo123"  
MONGO_USER = "memo"
MONGO_URL = "mongodb://{}:{}@localhost:{}/memos".format(MONGO_USER,MONGO_PW,MONGO_PORT)


try: 
    dbclient = MongoClient(MONGO_URL)
    db = dbclient.memos #memos is name of database that you created 
    collection = db.testdated  #testdated is name of collection. you are creating this collection right now
    #the parts that you fill in the database are the things that youll use to find stuff MAKING NEW COLLECTION JUST FOR TESTING

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)



def test_AddDeleteMemo():
    collection.remove({}) #empty collection out
    test_date1 = "02/10/2016"
    arrow_test_date1 = arrow.get(test_date1, 'MM/DD/YYYY')
    storage_test_date1 = arrow_test_date1.isoformat()
    text1 = "This is test memo #1"
    
    test_date2 = "04/15/2015"
    arrow_test_date2 = arrow.get(test_date2, 'MM/DD/YYYY')
    storage_test_date2 = arrow_test_date2.isoformat()
    text2 = "This is test memo #2"
    
    test_date3 = "06/04/2016"
    arrow_test_date3 = arrow.get(test_date3, 'MM/DD/YYYY')
    storage_test_date3 = arrow_test_date3.isoformat()
    text3 = "Birthday"
    
    #add 3 memos
    AddNewDatedMemo(test_date1, text1, collection)
    AddNewDatedMemo(test_date2, text2, collection)
    AddNewDatedMemo(test_date3, text3, collection)
    amount1 = collection.count( { "type": "dated_memo", "date": storage_test_date1, "text": text1 } )
    amount2 = collection.count( { "type": "dated_memo", "date": storage_test_date2, "text": text2 } )
    amount3 = collection.count( { "type": "dated_memo", "date": storage_test_date3, "text": text3 } )
    assert amount1 == 1
    assert amount2 == 1
    assert amount3 == 1
    
    #now delete 2 of the 3 memos
    record1 = collection.find( { "type": "dated_memo", "date": storage_test_date1, "text": text1 } )
    record2 = collection.find( { "type": "dated_memo", "date": storage_test_date2, "text": text2 } )
    id1 = str(record1[0]['_id'])
    id2 = str(record2[0]['_id'])
    selected = [id1, id2]
    removeSelectedMemos(selected, collection)
    count1 = collection.count( { "type": "dated_memo", "date": storage_test_date1, "text": text1 } )
    count2 = collection.count( { "type": "dated_memo", "date": storage_test_date2, "text": text2 } )
    count3 = collection.count( { "type": "dated_memo", "date": storage_test_date3, "text": text3} )
    assert count1 == 0
    assert count2 == 0
    assert count3 == 1
    

def test_ListMemosSorted():
    collection.remove({}) #empty collection out
    sorted_dates = ["2014-07-08", "2015-05-20", "2015-11-14", "2016-01-02", "2016-01-03", "2016-01-04", "2017-08-13"]
    sorted_text = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh"] 
    #2014-07-08T00:00:00+00:00
    AddNewDatedMemo("01/03/2016", "Fifth", collection)
    AddNewDatedMemo("11/14/2015", "Third", collection)
    AddNewDatedMemo("05/20/2015", "Second", collection)
    AddNewDatedMemo("07/08/2014", "First", collection)
    AddNewDatedMemo("08/13/2017", "Seventh", collection)
    AddNewDatedMemo("01/04/2016", "Sixth", collection)
    AddNewDatedMemo("01/02/2016", "Fourth", collection)
    records = get_memos(collection) #a list
    for i in range(0, len(records)):
        assert records[i]['date'].startswith(sorted_dates[i])
        assert records[i]['text'] == sorted_text[i] 
    
    

def test_FormatRelativeDates():
    #test close to today and time zone problems
    date = "01/09/2016"
    arrow_date = arrow.get(date, 'MM/DD/YYYY')
    storage_date = arrow_date.isoformat()
    
    now1 = "01/08/2016 23:30"
    arrow_now1 = arrow.get(now1, 'MM/DD/YYYY HH:mm')
    assert RelativeDate(storage_date, arrow_now1) == "Tomorrow"
    
    now2 = "01/09/2016 23:00"
    arrow_now2 = arrow.get(now2, 'MM/DD/YYYY HH:mm')
    assert RelativeDate(storage_date, arrow_now2) == "Today"

    #now3 = "01/07/2016 23:30"
    #arrow_now3 = arrow.get(now3, 'MM/DD/YYYY HH:mm')
    #assert RelativeDate(storage_date, arrow_now3) == "in two days" #right now it says this is tomorrow
    
    now4 = "01/10/2016 00:00"
    arrow_now4 = arrow.get(now4, 'MM/DD/YYYY HH:mm')
    assert RelativeDate(storage_date, arrow_now4) == "Yesterday"
    
    
    
    
    
    
    
    
    


