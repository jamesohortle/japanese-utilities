#!/usr/bin/local python3
# -*- coding: utf-8 -*-
"""Perform a fuzzy match of the transcriptions from the WAV files on the stripped and cleaned text."""

import pickle
from itertools import accumulate

import MeCab
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from normalize import normalizeSentence as normalize
from create_mappings import punctuationMapping

strippedSourceText = "./stripped.txt"
transcriptionsFilePath = "./transcriptions.txt"

# strippedSourceText = "./stripped_ch1.txt"
# transcriptionsFilePath = "./transcriptions_ch1.txt"

splittingChars = {"\n", "。"} # {"\n", "。", "　", "、"}
punctuation = set(map(chr, punctuationMapping.keys()))

def yieldSentences(filepath):
   """
   " Yield sentence-like strings.
   " Could do with a refactor for that pesky final yield.
   " Maybe use while loops instead...
   """
   with open(filepath, "r") as f:
      newSent = ""
      for line in f: # Go through lines of file.
         for char in line: # Go through chars of a line.
            if char: # Safety.
               newSent += char # Add the char.
               if char in splittingChars: # Yield if we're on a splitting char.
                  if newSent not in splittingChars: # But only if it's a non-trivial sentence.
                     yield newSent
                     newSent = "" # Reinitialize the sentence.
                  else: # Otherwise, reinitialize the sentence and try again.
                     newSent = ""
                     continue
      yield newSent # Yield final line.

def yieldPathsTranscriptions(filepath):
   """Yield paths and pre-computed transcriptions."""
   with open(filepath, "r") as f:
      for line in f:
         pairs = line.split("\t")
         path = pairs[0].strip()
         if len(pairs) > 1:
            transcription = pairs[1].strip()
         else:
            transcription = ""
         yield path, transcription

def findCandidates(t):
   """Find candidate sentences for a transcription."""
   tagger = MeCab.Tagger("-Oyomi")

   sentences = yieldSentences(strippedSourceText)

   candidates = []
   for s in sentences:

      # Surface-level similarity.
      normT = normalize(t)
      normS = normalize(s)
      if not (normT and normS):
         continue
      p = fuzz.partial_ratio(normT, normS)

      # Pronunciation-level similarity.
      yomiT = normalize(tagger.parse(t))
      yomiS = normalize(tagger.parse(s))
      q = 0.75 * fuzz.partial_ratio(yomiT, yomiS)

      # Combine the scores.
      r = (p + q) / 175 # (0 <= p + q <= 175)

      # Only consider if r >= 0.5.
      if r >= 0.5:
         candidates += [s]

   return candidates

def realign(parSent, fullSent):
   print(parSent, fullSent)
   tagger = MeCab.Tagger("-Owakati")

   # Get MeCab's 分かち書き as a list of blocks.
   splitSent = tagger.parse(fullSent).strip().split(" ")
   print(splitSent)

   # Verify nothing went wrong.
   if fullSent.strip() != ''.join(splitSent):
      raise RuntimeError("MeCab messed up the 分かち書き.")
   

def searchWindows(t, cs):
   """Search the windows from normalized candidates and return best match. Combines surface- and pronunciation-level information."""

   normT = normalize(t)
   normCs = list(map(normalize, cs))

   # Use MeCab for the pronunciations.
   tagger = MeCab.Tagger("-Oyomi")
   
   # Make the windows.
   absMaxDeviation = len(normT) // 2
   windowSizes = range(len(normT) - absMaxDeviation, len(normT) + absMaxDeviation)
   
   surfWindows = [
      (normC[i:i + size], normCs.index(normC))
      for normC in normCs
      for size in windowSizes
      for i in range(len(normC) - size + 1)
   ]

   pronWindows = [tagger.parse(w[0]).strip() for w in surfWindows]

   bestPron = process.extractOne(tagger.parse(normT), pronWindows, scorer=fuzz.ratio)

   if bestPron:
      # Use best pronunciation to get surface form, since indexing was preserved.
      best, source = surfWindows[pronWindows.index(bestPron[0])]
   else:
      # No good matches found in candidates (bestPron == None).
      best = ""
      source = -1
   
   # best = realign(best, cs[source])

   return best, source

def denormalize(best, candidate):
   """Recover the original characters/punctuation of the best match."""

   # Find potential head and tail indices.
   head = best[0]
   tail = best[-1]

   headInds = [i for i, c in enumerate(candidate) if c == head]
   tailInds = [i for i, c in enumerate(candidate) if c == tail]

   # Try all possible substrings.
   for h in headInds:
      for t in tailInds:

         # Return the candidate whose normalization matches.
         if normalize(candidate[h:t + 1]) == best:

            # Keep trailing punctuation.
            if candidate[t + 1] in (punctuation | splittingChars):
               return candidate[h:t + 2]
            else:
               return candidate[h:t + 1]

   # In case nothing matches, which is a possibility, return our best try.
   return best

def findBestMatch(t):
   """Check transcription against candidates and find the best match for each."""

   cs = findCandidates(t)

   normT = normalize(t)
   normCs = list(map(normalize, cs))
   best = ""
   source = -1
   if len(normCs) == 0: # No matches.
      best = ""
   elif len(normCs) == 1 and normT == normCs[0]: # "Perfect" matches.
      best = cs.pop()
   else: # Search for best match.
      best, source = searchWindows(t, cs)

   # Denormalize if needed.
   if source != -1:
      best = denormalize(best, cs[source])

   return best

def yieldBestMatches():
   """Find and yield best match for every transcription."""
   try:
      # Takes a while to calculate, so load the saved file instead.
      with open("list_bestMatches.pkl", "rb") as pickle_in:
         bestMatches = pickle.load(pickle_in)
   except FileNotFoundError:
      # Do the calculations and make the file if it doesn't exist.
      pathsTranscriptions = yieldPathsTranscriptions(transcriptionsFilePath)
      bestMatches = []
      for p, t in pathsTranscriptions:
         m = findBestMatch(t)
         print(p, t, m)
         bestMatches.append((p, t, m))
         yield p, t, m
      with open("list_bestMatches.pkl", "wb") as pickle_out:
         pickle.dump(bestMatches, pickle_out)
   else:
      # Yield from the successfully loaded list.
      yield from bestMatches

# def realign(subMatches, sent):
#    # print(subMatches, sent)
#    print(subMatches, sent)
#    tagger = MeCab.Tagger("-Owakati")

#    splitSent = tagger.parse(sent).strip().split(" ")
#    # print(splitSent)

#    # Verify nothing went wrong.
#    if sent.strip() != ''.join(splitSent):
#       raise RuntimeError("MeCab messed up the 分かち書き.")

#    # Make the splitting ranges.
#    ranges = []
#    start = 0
#    for block in accumulate(splitSent):
#       stop = len(block)
#       ranges.append((start, stop))
#       start = stop
#    # print(ranges)

#    # Make ranges into indexable list.
#    lranges = list(enumerate(ranges))

#    # Initialize.
#    alignedMatches = []
#    lastFound = 0

#    # Loop through subMatches.s
#    for subMatch in subMatches:
#       # print(subMatch)
#       # For each subMatch, find the 分かち書き blocks which compose it.
#       newString = ""
#       for i, r in lranges[lastFound:]:
#          newString += sent[r[0]:r[1]]
#          # print(newString, r)
#          # Is the block a superstring of the subMatch?
#          if subMatch in newString:
#             break

#       # Check cases and correct if needed.
#       if subMatch == newString:
#          # Perfect match, continue.
#          alignedMatches.append(subMatch)
#          lastFound = i + 1
#       elif len(subMatch) <= len(newString):
#          # Rewind the newString one block and append that.
#          alignedMatches.append(newString[:-(r[1] - r[0])])
#          lastFound = i
#       else:
#          # The current block has some junk in the front or is final part of sent.
#          if sent.endswith(newString) and subMatch.endswith(newString):
#             alignedMatches.append(newString)
#          else:
#             alignedMatches.append("")
#    print(alignedMatches)
#    return alignedMatches

# def yieldAlignedMatches():
#    """Align matches with the source text and yield the result."""

#    # Start the generators.
#    sourceText = yieldSentences(strippedSourceText)


#    # Go through sentences in the source text.
#    for sent in sourceText:

#       # Initialize matches for each sentence.
#       bestMatches = yieldBestMatches()
#       paths = []
#       transcriptions = []
#       subMatches = []

#       # Grab all matches in the sentence.
#       for p, t, m in bestMatches:
#          if m and m in sent and m not in subMatches:
#             paths.append(p)
#             transcriptions.append(t)
#             subMatches.append(m)

#       # Early exit if subMatches are perfect.
#       if ''.join(subMatches) is m.strip():
#          yield sent, paths, transcriptions, subMatches

#       # Otherwise, realign.
#       else:
#          yield sent, paths, transcriptions, realign(subMatches, sent)

# if __name__ == "__main__":
#    finalMatches = yieldAlignedMatches()

#    with open("out.txt", "w") as out:
#       for s, ps, ts, ms in finalMatches:
#          if not (len(ps) == len(ts) == len(ms)):
#             raise RuntimeError("Lengths are weird.")
#          for i, path in enumerate(ps):
#             if not (path and ts[i] and ms[i] and s):
#                print("Warning")
#                continue
#             # print(path, ts[i], ms[i], s)
#             newLine = "\t".join([path, ts[i], ms[i], s]) + "\n"
#             # print(newLine)
#             out.write(newLine)
