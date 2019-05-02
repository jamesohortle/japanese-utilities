#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Connect to the running Julius server and process a batch of files."""

import re
import socket
import sqlite3
import lxml.etree as ET
from time import sleep
from pathlib import Path
from subprocess import run, Popen

##############
# CONSTANTS. #
##############
# Socket-related.
HOST = "localhost"
PORT = 10500

# Tags/XML-related
INPUT_TAG = '<INPUT STATUS="LISTEN" '
RECOGOUT_TAG = 'RECOGOUT'
SENT_HYPO_TAG = 'SHYPO'
WORD_HYPO_TAG = 'WHYPO'
START_TAG = '<' + RECOGOUT_TAG + '>\n'
END_TAG = '</' + RECOGOUT_TAG + '>\n'
# TAGS = [RECOGOUT_TAG, SENT_HYPO_TAG, WORD_HYPO_TAG]

############
# REGEXES. #
############
# Helper regexes to escape angle brackets.
startClassId = re.compile(r"\"<s>\"")
endClassId = re.compile(r"\"</s>\"")

#####################################
# Functions for processing the XML. #
#####################################
# def startRecogMatch(line):
#    """Helper function to match the beginning of a recognition out tag."""
#    return True if line == START_TAG else False

def endRecogMatch(line):
   """Helper function to match the end of a recognition out tag."""
   return True if line == END_TAG else False

def escapeAngleBrackets(sentence):
   """Helper function to escape angle brackets in attribute values of XML tags."""
   return endClassId.sub(
      '"&lt;/s&gt;"',
      startClassId.sub(
         '"&lt;s&gt;"',
         sentence
      )
   )

def deleteBadLines(sentence):
   """Julius outputs lines with just a "." on them, which is not valid XML. Remove them."""
   sList = [s for s in sentence.split('\n') if s not in [".", ""]]
   return '\n'.join(sList)

def fixXML(sentence):
   """Apply some quick fixes to the XML so LXML can handle it."""
   sentence = escapeAngleBrackets(sentence)
   sentence = deleteBadLines(sentence)
   return "<CHUNK>\n" + sentence + "\n</CHUNK>"

def processSent(sentence):
   """Process a recognized sentence and print it."""
   if not sentence:
      return ''
   sentence = fixXML(sentence)
   root = ET.fromstring(sentence)
   recogs = root.findall(RECOGOUT_TAG)
   if not recogs:
      return ''
   else:
      sents = recogs[0].findall(SENT_HYPO_TAG)
      if not sents:
         return ''
      else:
         for sent in sents:
            if sent.attrib["RANK"] == "1":
               newSentence = ''.join(w.attrib["WORD"] for w in sent.findall(WORD_HYPO_TAG))
               return newSentence

########################################
# Generator for yielding lines of XML. #
########################################
def yieldLines(port):
   # Connect to the Julius server.
   # Julius will start processing the files.
   while True:
      try:
         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         s.connect((HOST, port))
      except socket.error:
         print(f"Retrying socket at {HOST}:{port}.")
         sleep(5)
      else:
         break

   # Make a file for the XML to be written to.
   s_write = s.makefile(mode='r')

   # Yield lines as they come in over the connection.
   for line in s_write:
      yield(line)

####################
# MAIN GENERATORS. #
####################
def yieldSentences(port):
   """Iterate over the XML from the socket and yield processed sentences."""
   lines = yieldLines(port)
   flag = False
   while True:
      try:
         if not flag:
            line = next(lines)
            flag = False
      except StopIteration:
         break
      else:
         if not line.startswith(INPUT_TAG):
            continue
         else:
            # Scan through and add everything until next INPUT_TAG.
            newSent = line
            while True:
               try:
                  line = next(lines)
                  if line.startswith(INPUT_TAG):
                     flag = True
                     break
               except StopIteration:
                  break
               else:
                  newSent += line
            yield processSent(newSent)

def yieldFilepaths(path):
   """Look at filelist.txt and yield filepaths."""

   # It feels shabby, but new sentences are generated in the same order
   # as the files in filelist.txt, so use that to zip them together.
   # (There must be a better way.)
   with open(path, 'r') as filelist:
      for line in filelist:
         yield line.strip()

def main(packedTuple):
   command, port, filelist = packedTuple

   # Start the Julius server.
   Popen(command)

   # Give the server enough time to start.
   sleep(10)

   # Read in the sentences.
   sentences = yieldSentences(port)

   # Generate the filenames.
   files = yieldFilepaths(str(filelist))

   # Make a database for each work to avoid locked databases in multiprocessing.
   dbPath = Path("../data", filelist.stem, "data.db")
   with sqlite3.connect(str(dbPath.resolve())) as conn:

      conn.execute(
      """
         CREATE TABLE IF NOT EXISTS file_transcriptions (
            file_path text UNIQUE,
            julius_transcription text,
            best_matches text,
            final_transcription text
         );
      """
   )
      for pair in zip(files, sentences):
         print(pair)
         try:
            conn.execute(
               """
                  INSERT INTO file_transcriptions (
                     file_path,
                     julius_transcription
                  )
                  VALUES (
                     ?,
                     ?
                  )
                  ;
               """,
               pair
            )
         except sqlite3.IntegrityError:
            conn.execute(
               """
                  UPDATE file_transcriptions
                  SET julius_transcription = ?
                  WHERE file_path = ?
                  ;
               """,
               tuple(reversed(pair))
            )
