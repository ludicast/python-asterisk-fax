#!/usr/bin/env python
import cgi
import cgitb; cgitb.enable()
import os, sys
import time
import socket

try:
  import msvcrt
  msvcrt.setmode(0, os.O_BINARY) # stdin  = 0
  msvcrt.setmode(1, os.O_BINARY) # stdout = 1
except ImportError:
  pass

UPLOAD_DIR="/var/www/cgi-bin/asterisk-fax/"

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
  <title>Asterisk Fax</title>
</head>
<body>
<form action="%(SCRIPT_NAME)s" enctype="multipart/form-data" method="post">
<table>
<tbody>
<tr>
  <td>File</td>
  <td><input name="fax" type="file" /></td>
</tr>
<tr>
  <td>Number</td>
  <td><input name="number" type="text" />&nbsp;<i>Ex.&nbsp;9371234567</i></td>
</tr>
</tbody>
</table>
<div>
<input name="submit" type="submit" value="Send Fax" />
<p>%(message)s</p>
</div>
</form>
</body>
</html>"""
  
def print_html_form(message):
  print "Content-Type: text/html\n"
  print HTML_TEMPLATE % {'SCRIPT_NAME':os.environ['SCRIPT_NAME'], 'message':message}

def save_uploaded_file(form_field, upload_dir):
  form = cgi.FieldStorage()
  if not form.has_key("submit"): return ""
  if not form[form_field].filename: return 'No file selected'
  if not form.has_key('number'): return 'No Fax number'
  if not form['number'].value: return 'No Fax number'
  fileitem = form[form_field]
  faxnumber = form["number"].value.strip()
  if not is_valid_filename(fileitem.filename):
    return "Invalid filetype: " + fileitem.filename
  if not is_valid_fax_number(faxnumber):
    return "Invalid fax number format: " + faxnumber
  if fileitem.file:
    fn = os.path.join(UPLOAD_DIR, str(time.time()) + '.tif')
    open(fn, 'wb').write(fileitem.file.read())
    message = "-"*15 + "&nbsp;<b>Fax Log</b>&nbsp;" + "-"*15 + "<br />" + fax(fn, faxnumber)
  else:
    message = 'No fax was sent'
  return message

def fax(fn, faxnumber):
  i = 0 + time.time()
  data = ""
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect(("127.0.0.1", 5038))

  sock.send("action: login\r\nusername: faxuser\r\nsecret: faxuser\r\nevents: on\r\nactionid: " + str(i) + "\r\n\r\n")
  i = i + 1
  data = buffer_response(sock, data)

  sock.send("action: originate\r\nchannel: DAHDI/G1/" + faxnumber + "\r\napplication: SendFAX\r\ndata: " + fn + "\r\nactionid: " + str(i) + "\r\n\r\n")
  i = i + 1
  data = buffer_response(sock, data)

  sock.send("action: logoff\r\nactionid: " + str(i) + "\r\n\r\n")
  data = buffer_response(sock, data)
  sock.close()
  return data

def is_valid_filename(fn):
  return fn.count('.tif',-4,len(fn))

def is_valid_fax_number(faxnumber):
  return faxnumber.isdigit() and len(faxnumber) == 10

def buffer_response(sock, data):
  file = sock.makefile('r+', 0)
  while True:
    line = file.readline().rstrip()
    if not line:
      break
    if line == "":
      break
    if line.count(':') == 0:
      break
    data = data + line + "<br />"
  return data + "<br />"

print_html_form(save_uploaded_file("fax", UPLOAD_DIR))
