#!/usr/bin/local/ python3
# -*- coding: utf-8 -*-
"""Try a new way of matching and aligning sentences by adding tags at appropriate places."""

import re
import sqlite3
from pathlib import Path
from multiprocessing import Pool

import MeCab
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from normalize import normalizeSentence as normalize


sentenceFinder = re.compile(r"(.*[。])")
def splitStrippedText(textPath):
   if textPath.is_file():
      with textPath.resolve().open(mode="r") as st:
         wholeText = st.read() # Luckily, none of the texts are too big to load into memory.
      return sentenceFinder.findall(wholeText)
   else:
      return []

def getSurfIndexes(cands, bestSurfCands):
   """Regain the indices of the best surface candidates from the candidates."""
   if not cands and bestSurfCands:
      return []
   enumSurfCands = enumerate(map(normalize, cands))

   indexes = []
   i = 0
   for bsc in bestSurfCands:
      for esc in enumSurfCands:
         if bsc[0] == esc[1] and esc[0] not in indexes:
            indexes.append(esc[0])
            break
      
      enumSurfCands = enumerate(map(normalize, cands))

   if len(indexes) == len(bestSurfCands):
      return indexes
   else:
      raise RuntimeError

yomiTagger = MeCab.Tagger("-Oyomi")
def getYomiIndexes(cands, bestYomiCands):
   """Regain the indices of the best reading candidates from the candidates."""
   if not cands and bestYomiCands:
      return []
   enumYomiCands = enumerate(map(normalize, map(yomiTagger.parse, cands)))

   indexes = []
   i = 0
   for byc in bestYomiCands:
      for eyc in enumYomiCands:
         if byc[0] == eyc[1] and eyc[0] not in indexes:
            indexes.append(eyc[0])
            break
      
      enumYomiCands = enumerate(map(normalize, map(yomiTagger.parse, cands)))

   if len(indexes) == len(bestYomiCands):
      return indexes
   else:
      raise RuntimeError

def judgePairs(surfTriples, yomiTriples, tInd, numTrans, numCands):
   """Return best surface form based on sum of weighted scores."""
   surfTriples = sorted(surfTriples, key=lambda s: s[0])
   yomiTriples = sorted(yomiTriples, key=lambda y: y[0])

   # Check lengths for error.
   if len(surfTriples) != len(yomiTriples):
      raise RuntimeError

   # Make sure that indices match.
   for i, s in enumerate(surfTriples):
      a = s[0]
      b = yomiTriples[i][0]
      if a != b:
         raise RuntimeError

   # Calculate the score for each pair and return the best surface form.
   scores = []
   for i, s in enumerate(surfTriples):
      p = s[2] # Surface.
      q = 0.75 * yomiTriples[i][2] # Pronunciation.
      
      t_rat = tInd / numTrans
      c_rat = s[0] / numCands
      r = 5 * (1 - abs(t_rat - c_rat)) # Relative positions.
      
      s = (p + q + r) / 180
      scores.append(s)
   return surfTriples[scores.index(max(scores))][0]

def sentenceLevelMatch(trans, tInd, numTrans, cands):
   """
    " Match a transcription to a sentence from the source text.
    " Use the following data.
    " i) the indices should be similar between the transcription
    "    and both surface and pronunciation forms,
    " ii) the surface forms should be similar,
    " iii) the pronunciations should be similar.
   """
   # print(trans)

   # Get surface candidates.
   normCands = map(normalize, cands)
   normTrans = normalize(trans)
   bestSurfCands = process.extractBests(normTrans, normCands, scorer=fuzz.partial_ratio)
   # print(bestSurfCands)
   surfIndexes = getSurfIndexes(cands, bestSurfCands)
   # print(surfIndexes)

   # Get pronunciation candidates.
   yomiCands = map(normalize, map(yomiTagger.parse, cands))
   yomiTrans = normalize(yomiTagger.parse(trans))
   bestYomiCands = process.extractBests(yomiTrans, yomiCands, scorer=fuzz.ratio)
   # print(bestYomiCands)
   yomiIndexes = getYomiIndexes(cands, bestYomiCands)
   # print(yomiIndexes)

   # Check indexes.
   commonIndexes = set(surfIndexes) & set(yomiIndexes)
   if len(commonIndexes) == 0:
      # Nothing found with confidence.
      return -1, ""
   elif len(commonIndexes) == 1:
      # Return the only common match's surface form.
      commonSent = bestSurfCands[surfIndexes.index(commonIndexes.pop())][0]
      for i, normCand in enumerate(map(normalize, cands)):
         if normCand == commonSent:
            return i, cands[i]
   else:
      # Calculate weighted score for (surf, yomi) pairs.
      i = judgePairs(
         [
            s
            for s in zip(
               surfIndexes,
               map(lambda bsc: bsc[0], bestSurfCands),
               map(lambda bsc: bsc[1], bestSurfCands))
            if s[0] in commonIndexes
         ],
         [
            y
            for y in zip(
               yomiIndexes,
               map(lambda byc: byc[0], bestYomiCands),
               map(lambda byc: byc[1], bestYomiCands)
            )
            if y[0] in commonIndexes],
            tInd,
            numTrans,
            len(cands)
      )
      return i, cands[i]

def makeMatches(workPath):
   if not workPath.is_dir(): return

   print(str(workPath.resolve()))

   dbPath = workPath / "data.db"
   if not dbPath.is_file():
      # print(f"There is no database: {dbPath.resolve()}")
      return

   strippedTextPath = workPath / "stripped_text" / "stripped.txt"
   cands = splitStrippedText(strippedTextPath)

   with sqlite3.connect(str(dbPath.resolve())) as conn:
      try:
         conn.execute(
            """
               ALTER TABLE file_transcriptions
               ADD COLUMN source_index INTEGER;
            """
         )
      except sqlite3.OperationalError as e:
         print(str(e) + f"; in {dbPath.resolve()}")
         pass

      maxRowId = conn.execute(
         """
            SELECT max(rowid)
            FROM file_transcriptions;
         """
      )
      numTrans = maxRowId.fetchone()[0]

      results = conn.execute(
         """
            SELECT rowid, file_path, julius_transcription
            FROM file_transcriptions
            ORDER BY file_path;
         """
      )
      for r in results:
         match = sentenceLevelMatch(r[2], r[0], numTrans, cands)
         conn.execute(
            """
               UPDATE file_transcriptions
               SET 
                  source_index = ?,
                  best_matches = ?
               WHERE
                  file_path = ?
               ;
            """,
            (match[0], match[1] if match[1] else None, r[1])
         )

dataPath = Path("../data")
pool = Pool()
pool.map(makeMatches, dataPath.iterdir())
pool.close()
pool.join()

# for p in dataPath.iterdir():
#    makeMatches(p)