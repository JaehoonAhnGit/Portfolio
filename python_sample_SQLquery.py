### PYTHON CODE
### Course search link to SQL 
### Jaehoon Ahn

from math import radians, cos, sin, asin, sqrt
import sqlite3
import json
import re
import os

# Use this filename for the database
DATA_DIR = os.path.dirname(__file__)
DATABASE_FILENAME = os.path.join(DATA_DIR, 'course-info.db')

empty_dict = {}

args_from_ui = {
  "terms": "science mathematics economics",
  "day": ["MWF"],
  "time_start": 900,
  "time_end": 1500
}


def find_courses(args_from_ui):
  '''
  Takes a dictionary containing search criteria and returns courses
  that match the criteria.  The dictionary will contain some of the
  following fields:

    - dept a string
    - day is array with variable number of elements  
         -> ["'MWF'", "'TR'", etc.]
    - time_start is an integer in the range 0-2359
    - time_end is an integer an integer in the range 0-2359
    - enroll is an integer
    - walking_time is an integer
    - building ia string
    - terms is a string: "quantum plato"]

  Returns a pair: list of attribute names in order and a list
  containing query results.
  '''
  conn = sqlite3.connect(DATABASE_FILENAME)
  conn.create_function("time_between", 4, compute_time_between)
  c = conn.cursor()

  sql_statement = get_sql_query(args_from_ui)[0]
  sql_argument = get_sql_query(args_from_ui)[1]

  if not (sql_statement and sql_argument): 
    return ([], [])
  else: 
    sql_query = c.execute(sql_statement, sql_argument)

  final_header = get_header(c)
  final_output = sql_query.fetchall()
  final_output = list(set(final_output))

  return (final_header, final_output)


def get_sql_query(args_from_ui):
  '''
  Takes a dictionary containing search criteria and returns sql statement and
  argument parameters matchign the search criteria
  Input: 
    args_from_ui(dict): arguments from the user/Django
  Output: 
    sql_query(tuple): (sql_statement(string), sql_argument(list))
  '''  
  attributes = select_attributes(args_from_ui)
  if not attributes: 
    return ("", [])
  
  SELECT = "SELECT " + ", ".join(attributes)
  FROM = "FROM courses JOIN sections JOIN meeting_patterns JOIN catalog_index"
  ON = "ON courses.course_id = sections.course_id\
        AND sections.meeting_pattern_id = meeting_patterns.meeting_pattern_id\
        AND courses.course_id = catalog_index.course_id"

  if "building" in args_from_ui: 
    FROM +=" JOIN gps AS a JOIN gps AS b"
    ON += " AND sections.building_code = a.building_code"

  WHERE_stmnt = sql_where(args_from_ui)[0]
  sql_argument = sql_where(args_from_ui)[1]

  sql_statement = SELECT+" "+FROM+" "+ON+" "+WHERE_stmnt
  
  if "terms" in args_from_ui:
    GROUP_BY = "GROUP BY courses.title, sections.section_id"
    HAVING_COUNT = "HAVING COUNT(DISTINCT catalog_index.word) >= ?"
    
    word_string = args_from_ui["terms"]
    word_list = word_string.split()

    sql_statement += " "+GROUP_BY+" "+HAVING_COUNT 
    sql_argument.append(len(word_list))

  return (sql_statement, sql_argument)


def sql_where(args_from_ui):
  '''
  Returns the WHERE portion of sql statement
  Input: 
    args_from_ui(dict): arguments from the user/Django
  Output:
    where_final(tuple): (where_statement(str), where_args(list)) 
  ''' 
  where_query = [] 
  for key, value in args_from_ui.items(): 
    if key == "terms": #', '.join('"{0}"'.format(w) for w in words)
      word_string = args_from_ui["terms"]
      word_list = word_string.split() #how to take the words_list out?
      word_param = "(" + ' ,'.join('"{0}"'.format(w) for w in word_list) + ")"
      where_query.append((0, "catalog_index.word IN " + word_param))
    if key == "dept":
      where_query.append((1, "courses.dept = ?", value))
    if key == "day":
      day_list = args_from_ui["day"]
      day_query = []
      for day in day_list: #this gets complicated 
          day_query.append("meeting_patterns.day = ?")
      day_query_string = " OR ".join(day_query)
      where_query.append((2, "("+day_query_string+")", day_list))
    if key == "time_start":
      where_query.append((3, "meeting_patterns.time_start >= ?", value))
    if key == "time_end":
      where_query.append((4, "meeting_patterns.time_end <= ?", value))
    if key == "building": 
      where_query.append((5, "b.building_code = ?", value))
    if key == "walking_time": 
      where_query.append((6, "walking_time <= ?", value))
    if key == "enroll_lower": 
      where_query.append((7, "sections.enrollment >= ?", value))
    if key == "enroll_upper": 
      where_query.append((8, "sections.enrollment <= ?", value))
  
  where_query.sort()
  where_commands = []
  where_args = []
  for query in where_query: 
    command = query[1] 
    where_commands.append(command)
    if query[0] == 0: #terms query 
      pass
    elif query[0] == 2: #day query 
      args = query[2]
      for arg in args: 
        where_args.append(arg) 
    else: 
      args = query[2]
      where_args.append(args)
  
  where_statement = "WHERE " + " AND ".join(where_commands)

  return (where_statement, where_args) 

def select_attributes(args_from_ui): 
  '''
  Returns a list of attributes
  Input: 
    args_from_ui(dict): arguments from the user/Django
  Output: 
    attributes(list): list of attributes
  '''
  attributes = ["na"]*10  

  for key in args_from_ui: 
    if key in ["terms", "dept", "day", "time_start", "time_end",\
              "walking_time", "building", "enroll_lower", "enroll_upper"]:
      attributes[0] ="courses.dept"
      attributes[1] = "courses.course_num"
    if key in ["terms", "dept"]: 
      attributes[9] = "courses.title"
    if key in ["day", "time_start", "time_end", "walking_time"\
              "building", "enroll_lower", "enroll_upper"]:
      attributes[2] = "sections.section_num"
      attributes[3] = "meeting_patterns.day"
      attributes[4] = "meeting_patterns.time_start"
      attributes[5] = "meeting_patterns.time_end"       
    if key in ["walking_time", "building"]:   
      attributes[6] = "sections.building_code"
      attributes[7] = "time_between(a.lat, a.lon, b.lat, b.lon) AS walking_time" 
    if key in ["enroll_lower", "enroll_upper"]: 
      attributes[8] = "sections.enrollment"
    
  attributes = [att for att in attributes if att != "na"]
  
  return attributes 

########### auxiliary functions #################
########### do not change this code #############

def compute_time_between(lon1, lat1, lon2, lat2):
    '''
    Converts the output of the haversine formula to walking time in minutes
    '''
    meters = haversine(lon1, lat1, lon2, lat2)

    #adjusted downwards to account for manhattan distance
    walk_speed_m_per_sec = 1.1 
    mins = meters / (walk_speed_m_per_sec * 60)

    return mins


def haversine(lon1, lat1, lon2, lat2):
    '''
    Calculate the circle distance between two points 
    on the earth (specified in decimal degrees)
    '''
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 

    # 6367 km is the radius of the Earth
    km = 6367 * c
    m = km * 1000
    return m 



def get_header(cursor):
    '''
    Given a cursor object, returns the appropriate header (column names)
    '''
    desc = cursor.description
    header = ()

    for i in desc:
        header = header + (clean_header(i[0]),)

    return list(header)


def clean_header(s):
    '''
    Removes table name from header
    '''
    for i in range(len(s)):
        if s[i] == ".":
            s = s[i+1:]
            break

    return s


########### some sample inputs #################

example_0 = {"time_start":930,
             "time_end":1500,
             "day":["MWF"]}

example_1 = {"building":"RY",
             "dept":"CMSC",
             "day":["MWF", "TR"],
             "time_start":1030,
             "time_end":1500,
             "enroll_lower":20,
             "terms":"computer science"}

