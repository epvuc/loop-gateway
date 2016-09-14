#
#   messager - utility functions
#
#   Part of baudotrss
#
import re
#
#   Utility functions
#
def edittime(dt) :
    """
    Edit time into "3:02 PM"
    """
    s = dt.strftime("%I:%M %p")                 # "07:30 PM"
    s = re.sub(r'^0+','',s)                     # "7:30 PM"
    return(s)
    msgdate = timestamp.strftime("%B %d")       # "March 12"
    
DAYSUFFIX = {"1" : "st", "2" : "nd", "3" : "rd" }   # special case date suffixes

def editdate(dt) :
    """
    Blah.
    """
    s=dt.strftime("%b %d, %Y")
    return(s)
