#!/usr/bin/local python3
# -*- coding: utf-8 -*-
"""Normalize a sentence."""

import re
from unicodedata import normalize

import create_mappings as maps

# def allAsciiToHalfwidth(sentence):
#    """Convert all fullwidth ASCII in sentence to halfwidth."""
#    newSent = sentence.translate(maps.asciiFullToHalfMapping)
#    return newSent


# def normalizeAscii(sentence):
#    """Normalize all ASCII."""
#    newSent = allAsciiToHalfwidth(sentence).lower()
#    return newSent

# def allJapaneseToFullwidth(sentence):
#    """Convert all halfwidth Japanese in sentence to fullwidth."""
#    newSent = sentence.translate(maps.japHalfToFullMapping)
#    return newSent

def replacePunctuation(sentence):
   """Replace all characters considered as punctuation with a space."""
   newSent = sentence.translate(maps.punctuationMapping)
   return newSent

# ASCII: \u0020-\u007F
# Hiragana: \u3041-\u3096
# Katakana: \u30A0-\u30FF
# Han: \u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A
nonAsciiKanaKanji = re.compile(r"[^\u0020-\u007F\u3041-\u3096\u30A0-\u30FF\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A\u3005]")
def replaceNonAsciiKanaKanji(sentence):
   """Replace all characters that are not ASCII, kana or kanji with a space."""
   newSent = nonAsciiKanaKanji.sub(" ", sentence)
   return newSent

multiWhitespace = re.compile(r"\s+")
def cleanWhitespace(sentence):
   """Clean whitespace by retaining only single spaces, replacing all other whitespace with a single space and stripping ends of string."""
   newSent = multiWhitespace.sub(" ", sentence).strip()
   return newSent

japaneseWhitespace = re.compile(r"([^\u0020-\u007F]\s+)+[^\u0020-\u007F]")
def deleteSpacesWithinJapanese(sentence):
   """Find spaces within Japanese text and remove them."""
   newSent = sentence
   for match in japaneseWhitespace.finditer(sentence):
      substr = match.group(0)
      newSubstr = multiWhitespace.sub("", substr)
      newSent = newSent.replace(substr, newSubstr)
   return newSent

def normalizeSentence(sentence):
   """Normalize a string by running through helper functions in order."""
   sentence = normalize("NFKC", sentence)
   # sentence = normalizeAscii(sentence)
   # sentence = allJapaneseToFullwidth(sentence)
   sentence = replacePunctuation(sentence)
   sentence = replaceNonAsciiKanaKanji(sentence)
   sentence = cleanWhitespace(sentence)
   sentence = deleteSpacesWithinJapanese(sentence)
   return sentence.strip()
