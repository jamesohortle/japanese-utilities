#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""List all sound files in data and put in data.db for processing. Create filelist.txt for Julius."""

import sqlite3
from pathlib import Path

def yieldInts():
   i = 0
   while True:
      yield i
      i += 1

filelistDir = Path("./filelists")
if not filelistDir.is_dir():
   filelistDir.mkdir()

dataPath = Path("../data")
dbPath = dataPath / "data.db"

newInt = yieldInts()

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

   
   for work in sorted(dataPath.iterdir()):
      if work.is_dir():
         filelistPath = filelistDir / f"./{str(work).split('/')[-1].strip()}.txt"
         with filelistPath.open(mode="w") as filelist:
            soundDir = work / "split_audio"
            if soundDir.is_dir():
               for soundFile in sorted(soundDir.iterdir()):
                  if soundFile.is_file() and soundFile.suffix == ".wav":
                     try:
                        conn.execute(
                           """
                              INSERT INTO file_transcriptions(file_path)
                              VALUES (?);
                           """,
                           (str(soundFile.resolve()),)
                        )
                     except sqlite3.IntegrityError:
                        pass

                     filelist.write(str(soundFile.resolve()) + "\n")
