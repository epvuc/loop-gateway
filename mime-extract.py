#!/usr/bin/python
                                                                                
import email                                                                    
import sys                                                                      
                                                                                
def output_message(msg):                                                        
  if msg.is_multipart():                                                        
    for part in msg.get_payload():                                              
      output_message(part)                                                      
  else:                                                                         
    if "text/plain" == msg.get_content_type():                                  
      print msg.get_payload(decode=True)                                        
                                                                                
if __name__ == "__main__":                                                      
  output_message(email.message_from_file(sys.stdin))                        
