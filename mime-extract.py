#!/usr/bin/python
                                                                                
import email                                                                    
import sys                                                                      
import subprocess
import re
        
def decrypt_pgp(txt):
  p = subprocess.Popen(['/usr/bin/gpg2'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  result = p.communicate(input=txt)
  decrypt = ''
  # first show info output from gpg itself
  if result[1]:
    decrypt = decrypt + result[1].replace('\n', '\r\n') + "\r\n"
  # next show the decrypted body minus initial "Content-*" headers
  if result[0]:
    for line in result[0].splitlines():
      if not re.match("Content-.*: .*", line):
        decrypt = decrypt + line + "\r\n"
  else:
    decrypt = decrypt +  "No message body.\r\n"
  return decrypt

def output_message(msg):                                                        
  pgp_coming = False
  if msg.is_multipart():                                                        
    #print "Message is multipart."
    for part in msg.get_payload():                                              
      #print "content-type is", part.get_content_type()
      if part.get_content_type() == "application/pgp-encrypted":
        pgp_coming = True
      if pgp_coming == True and part.get_content_type() == "application/octet-stream":
        print decrypt_pgp(part.get_payload(decode=True))
      else:
        output_message(part)                                                      
  else:                                                                         
    #print "Message is not multipart."
    if '-----BEGIN PGP MESSAGE-----' in msg.get_payload(decode=True):
      print decrypt_pgp(msg.get_payload(decode=True))
    else:
      if "text/plain" == msg.get_content_type(): 
        print msg.get_payload(decode=True)
                                                                                
if __name__ == "__main__":                                                      
  output_message(email.message_from_file(sys.stdin))                        
