APDIncidentReportsScraper
=========================

Scrape the Austin Police Department's messy Indcident Reports Database (police reports) into a machine-readable CSV format. Reports come from the official APD website: https://www.austintexas.gov/police/reports/index.cfm

# Usage

Pretty simple ...

`apd_incident_reports.py [-h] [--verbose] STARTDATE ENDDATE FILENAME`

In detail:

`Arguments:
  STARTDATE   Date to start scraping from (furthest date from present) in
              MM/DD/YYYY format.
  ENDDATE     Date to scrape to (nearest to now) in MM/DD/YYYY format.
  FILENAME    Filename to write CSV data to.

Optional Arguments:
  --verbose   Increase output verbosity`

# Notes

- The Austin Police Department only holds the past 18 months of police reports on their site, get it while it lasts.

- There is no way to disinguish between non-Hispanic whites and Hispanic whites in the reports. The APD doesn't include ethnicity data here, so all Hispanic people are lumped into "White".

- Juvenile offenders' names are censored from the reports.

- I use Aaron Swartz's `html2txt` https://github.com/aaronsw/html2text