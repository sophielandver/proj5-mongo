"""
Nose tests for flask_main.py
"""
import arrow
from flask_main import AddNewDatedMemo
from flask_main import removeSelectedMemos 
from flask_main import get_memos
from flask_main import humanize_arrow_date
from flask_main import RelativeDate

from pymongo import MongoClient
import CONFIG

try: 
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.memos #memos is name of database that you created 
    collection = db.testdated  #dated is name of collection. you are creating this collection right now

except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    sys.exit(1)



def test_AddDeleteMemo():
    """
    Test adding memos into database and deleting memos from database. 
    """
    collection.remove({}) #empty collection out
    test_date1 = "02/10/2016"
    arrow_test_date1 = arrow.get(test_date1, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_test_date1 = arrow_test_date1.isoformat()
    text1 = "This is test memo #1"
    
    test_date2 = "04/15/2015"
    arrow_test_date2 = arrow.get(test_date2, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_test_date2 = arrow_test_date2.isoformat()
    text2 = "This is test memo #2"
    
    test_date3 = "06/04/2016"
    arrow_test_date3 = arrow.get(test_date3, 'MM/DD/YYYY').replace(tzinfo='local')
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
    """
    Test listing the memos from the database in sorted order by date.
    """
    collection.remove({}) #empty collection out
    sorted_dates = ["2014-07-08", "2015-05-20", "2015-11-14", "2016-01-02", "2016-01-03", "2016-01-04", "2017-08-13"]
    sorted_text = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh"] 
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
    """
    Test date formatting, especially for dates close to today. Also, test potential 
    time zone issues. 
    """
    #test close to today and time zone problems
    now = "02/11/2016"
    arrow_now = arrow.get(now, 'MM/DD/YYYY').replace(tzinfo='local').replace(hour=0)
    
    date1 = "02/11/2016"
    arrow_date1 = arrow.get(date1, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_date1 = arrow_date1.isoformat()
    assert RelativeDate(storage_date1, arrow_now) == "Today"
    
    date2 = "02/12/2016"
    arrow_date2 = arrow.get(date2, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_date2 = arrow_date2.isoformat()
    assert RelativeDate(storage_date2, arrow_now) == "Tomorrow"
    
    date3 = "02/10/2016"
    arrow_date3 = arrow.get(date3, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_date3 = arrow_date3.isoformat()
    assert RelativeDate(storage_date3, arrow_now) == "Yesterday"
    
    date4 = "02/13/2016"
    arrow_date4 = arrow.get(date4, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_date4 = arrow_date4.isoformat()
    assert RelativeDate(storage_date4, arrow_now) == "in 2 days"
    
    date5 = "02/09/2016"
    arrow_date5 = arrow.get(date5, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_date5 = arrow_date5.isoformat()
    assert RelativeDate(storage_date5, arrow_now) == "2 days ago"
    
    date6 = "02/18/2016"
    arrow_date6 = arrow.get(date6, 'MM/DD/YYYY').replace(tzinfo='local')
    storage_date6 = arrow_date6.isoformat()
    assert RelativeDate(storage_date6, arrow_now) == "in 7 days"
    

    

