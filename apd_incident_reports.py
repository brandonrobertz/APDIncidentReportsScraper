#!/usr/bin/python
"""apd_incident_reports: Scrape the APD's messy indcident reports database 
into a machine-readable format."""
__version__   = "2.0"
__author__    = "Brandon Roberts (brandon@austincut.com)"
__copyright__ = "(C) 2012 B Roberts. GNU GPL 3+"

import sys
import argparse
import re
import requests
import csv
from datetime import datetime, timedelta, date
from html2text import html2text

def process_report( html, verbose=False):
  """ This parses the messy APD Incidents Reports page and spits out the
      information about those who were arrested.

      Paramaters:
        txt : The raw html APD reports page

      Returns
        a generator object containing lists of everyone arrested in the
        following format:
          [ report, date, name, dob, sex, race, crime, summary, location]
  """
  txt = html2text( html) # this can take a min if the page is huge
  txtf = re.sub( r"[\r\n]+", "\n", txt)
  for incident in re.split(r'End Of Offense', txtf):
    if "Arrestee" not in incident: continue # skip if there's no arrestee(s)
    n = 0 # we use this to track which line we're on, because in some cases
          # the info we want is on a following line, not the one we're on
    date    = ""
    name    = ""
    dob     = ""
    sex     = ""
    race    = ""
    crime   = ""
    summary = ""
    report  = ""
    s = re.split(r"[\r\n]+", incident)
    # get info about the incident
    for l in s:
      if "offense date/time" in l.lower():
        date = s[n+1] 
      elif "offense location" in l.lower():
        location = s[n+1] 
      elif "case summary" in l.lower():
        if "*" not in s[n+1]:
          x = 0
          f = True
          try:
            while "*" not in s[n+1+x]:
              if f:
                summary = s[n+1+x]
                f = False
              else:          
                summary = summary + " " + s[n+1+x]
              x=x+1
          except:
            pass
        else:
          summary = ""
      elif "report number" in l.lower():
        report = s[n+1]
      elif "offense(s)" in l.lower():
        x = 0
        f = True
        while "*" not in s[n+1+x]:
          if f:
            crime = s[n+1+x]
            f = False
          else:          
            crime = crime + ", " + s[n+1+x]
          x=x+1
      n=n+1
    #now get everyone who was arrested, there can be multiple per report
    n = 0
    for l in s:
      if "arrestee" in l.lower():
        report   = re.sub(r'"',"\"", report).strip()
        date     = re.sub(r'"',"\"", date).strip()
        name     = re.sub(r'\*+[^)]*\*+:', '', s[n+1]).strip()
        dob      = re.sub(r'\*+[^)]*\*+:', '', s[n+2]).strip()
        sex      = re.sub(r'\*+[^)]*\*+:', '', s[n+3]).strip()
        race     = re.sub(r'\*+[^)]*\*+:', '', s[n+4]).strip()
        location = re.sub(r'"',"\"", location).strip()
        summary  = re.sub(r'"',"\"", summary).strip()
        line = [ report, date, name, dob, sex, race, crime, summary, location]
        if verbose:
          print "\t%s %s %s %s %s %s %s %s %s"%( report, date, name, 
                                                 dob, sex, race, crime,
                                                 summary, location)
        yield line
      n=n+1

def write_csv( data, filename, verbose=False):
  """ Write our CSV arrests file to disk.

      Parameters:
        data : an iterable containing lists in the following format
          [ report, date, name, dob, sex, race, crime, summary, location]
  """
  if verbose:
    print "[*] Writing to %s"%filename
  with open(filename, 'wb') as f:
    header = [ "report", "date", "name", "dob", "sex",
               "race", "crime", "summary", "location" ]
    w = csv.writer(f, header)
    w.writerow( header)
    w.writerows( data)

def yield_reports( STARTDATE, ENDDATE, verbose=False):
  """ Get APD Incident Report for specified DATE. Note: The APD Incident
      reports database only holds around 18 months of recent arrest data.
      Also, juvenile offenders have their names censored.

      Parameters:
        STARTDATE : A date object specifying the date we want to
                    start with (nearest in time)

        ENDDATE : A date object specifying the last day we want to grab
                  (furthest back in time)

      Returns:
        A generator of lists containing information about people who were
        arrested on and between the input dates.
  """
  SITE="https://www.austintexas.gov/police/reports/search2.cfm"
  day_count = (STARTDATE - ENDDATE).days + 1 # include end date
  for date in (STARTDATE - timedelta(n) for n in range(day_count)):
    # Format Date
    DATE = re.sub("-","/", "%s"%date)
    if verbose:
      print "[*] Date:", DATE
    PARAMS = ("?startdate=%s&numdays=0&address=&rucrext="
              "&tract_num=&zipcode=&zone=&district=&city=AUSTIN"
              "&choice=criteria&Submit=Submit"%DATE)
    URL = "%s%s"%(SITE,PARAMS)
    if verbose:
      print "[*] URL:", URL
    # get page
    try:
      r = requests.get(URL)
    except Exception as e:
      print "[!] Error %s on %s"%(e, URL)
    # return if good
    if r.status_code == 200:
      # Process it
      for a in process_report( r.text, verbose):
        yield a

def incident_reports( STARTDATE, ENDDATE, FILENAME, verbose=False):
  """ Write all APD arrests found between STARTDATE and ENDDATE to
      a CSV file names filename.

      Paramaters:
        STARTDATE : A date object specifying the date we want to
                    start with (nearest in time)

        ENDDATE : A date object specifying the last day we want to grab
                  (furthest back in time)

        FILENAME : filename to write CSV to
  """
  reports = yield_reports( STARTDATE, ENDDATE, verbose)
  write_csv( reports, FILENAME, verbose)

if __name__ == "__main__":
  # cmd line args
  desc = ( "Scrape the APD's messy indcident reports database into a"
           "machine-readable format.")
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument("STARTDATE", help= "Date to start scraping from"
                                         "(furthest date from present) in "
                                         "MM/DD/YYYY format.")
  parser.add_argument("ENDDATE", help= "Date to scrape to (nearest to now) "
                                       "in MM/DD/YYYY format.")
  parser.add_argument("FILENAME", help="Filename to write CSV data to.")
  parser.add_argument("--verbose", help="Increase output verbosity",
                    action="store_true")
  args = parser.parse_args()

  # greetz
  print "   #################################"
  print "   #  APD Incident Reports Scraper #"
  print "   #################################"

  # convert the dates from strings to datetime objects
  try:
    sd = datetime.strptime( args.STARTDATE, "%m/%d/%Y")
    ed = datetime.strptime( args.ENDDATE,   "%m/%d/%Y")
    FILENAME  = args.FILENAME
  except ValueError:
    print( "[!] ERROR! Make sure you formatted the start and end dates"
           "correctly: MM/DD/YYYY")
    sys.exit()

  # convert to date objects
  STARTDATE = date( sd.year, sd.month, sd.day)
  ENDDATE   = date( ed.year, ed.month, ed.day)

  # print some info and go!
  print "[*] Scraping dates from %s to %s and saving as %s"%( ENDDATE,
                                                              STARTDATE,
                                                              FILENAME)
  incident_reports( STARTDATE, ENDDATE, FILENAME, args.verbose)
  print "[*] Boom shucka lucka. (Done)"