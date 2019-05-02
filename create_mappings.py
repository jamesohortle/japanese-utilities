#!/usr/bin/local python3
# -*- coding: utf-8 -*-
"""Create efficient character mappings to help with normalization."""

import re
import string
import pickle

from itertools import chain

###########################################
# Fullwidth ASCII to halfwidth ASCII map. #
###########################################

try:
   # Load the mapping.
   with open('map_asciiFullToHalfMapping.pkl', 'rb') as in_mapping:
      asciiFullToHalfMapping = pickle.load(in_mapping)
except FileNotFoundError:
   # Combine Unicode ranges to make a mapping from fullwidth to halfwidth.
   asciiFullToHalfMapping = str.maketrans( # Make a mapping from the dictionary.
      dict( # Make a dictionary from the tuples.
         zip( # Make tuples from the corresponding characters.
            chain(
               ["　"], # Fullwidth space.
               map( # Map the numerical values to characters.
                  chr, # E.g., chr(0x0020) == " ".
                  chain(
                     range(0xFF01, 0xFF61), #\uFF00 = "！", ..., \uFF60 = "｠"
                     range(0xFFE0, 0xFFE7) #\uFFE0 = "￠", ..., \uFFE7 = "￦"
                  )
               ),
               ["〇"] #Ideographic zero.
            ),
            chain(
               map(
                  chr,
                  chain(
                     range(0x0020, 0x007F), #\u0200 = ' ', ..., \u007f = "~"
                     [0x2985, 0x2986, 0x00A2, 0x00A3, 0x00AC, 0x00AF, 0x00A6, 0x00A5, 0x20A9] # \u2985 = "⦅", ..., \u20A9 = ₩
                  )
               ),
               ["0"]
            )
         )
      )
   )

   # Save the mapping.
   print(asciiFullToHalfMapping)
   with open('map_asciiFullToHalfMapping.pkl', 'wb') as out_mapping:
      pickle.dump(asciiFullToHalfMapping, out_mapping)

#################################################
# Halfwidth Japanese to fullwidth Japanese map. #
#################################################

try:
   # Load the mapping.
   with open('map_japHalfToFullMapping.pkl', 'rb') as in_mapping:
      japHalfToFullMapping = pickle.load(in_mapping)
except FileNotFoundError:
   # Combine Unicode ranges to make a mapping from fullwidth to halfwidth.
   japHalfToFullMapping = str.maketrans( # Make a mapping from the dictionary.
      dict( # Make a dictionary from the tuples.
         zip( # Make tuples from the corresponding characters.
            map( # Map the numerical values to characters.
               chr, # E.g., chr(0xFF61) == "｡".
               chain(
                  range(0xFF61, 0xFFA0), #\uFF61 = "｡", ..., \uFF9F = "ﾟ"
                  range(0xFFE8, 0xFFEF) #\uFFE8 = "￨", ..., \uFFEE = "￮"
               )
            ),
            [
               "。", "「", "」", "、", "・",
               "ヲ",
               "ァ", "ィ", "ゥ", "ェ", "ォ", "ャ", "ュ", "ュ", "ッ", "ー",
               "ア", "イ", "ウ", "エ", "オ",
               "カ", "キ", "ク", "ケ", "コ",
               "サ", "シ", "ス", "セ", "ソ",
               "タ", "チ", "ツ", "テ", "ト",
               "ナ", "ニ", "ヌ", "ネ", "ノ",
               "ハ", "ヒ", "フ", "ヘ", "ホ",
               "マ", "ミ", "ム", "メ", "モ",
               "ヤ", "ユ", "ヨ",
               "ラ", "リ", "ル", "レ", "ロ",
               "ワ", "ン",
               "゛", "゜",
               "｜", "←", "↑", "→", "↓", "■", "○"
            ]
         )
      )
   )

   # Save the mapping.
   print(japHalfToFullMapping)
   with open('map_japHalfToFullMapping.pkl', 'wb') as out_mapping:
      pickle.dump(japHalfToFullMapping, out_mapping)

###########################################################
# Set of characters considered punctuation maps to space. #
###########################################################

# ASCII punctuation, CJK punctuation, quotation marks, historical punctuation marks, ...
# See https://unicode-table.com/en/search/?q=punctuation
# There are definitely duplicates below, so we use sets to get rid of them.
# Most fonts can't represent all characters, so we use lots of escapes.
# NB.: None of the characters here should overlap with whitespace.
try:
   with open("map_punctuationMapping.pkl", "rb") as mapping_in:
      punctuationMapping = pickle.load(mapping_in)
except FileNotFoundError:
   punctuation = \
      set(string.punctuation) | \
      set("！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠［＼］＾＿｀｛｜｝～、。〃〈〉《》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟｟｠｡｢｣､･゠〰⦅⦆") | \
      set("«‹»›„‚“‟‘‛”’❛❜\u275F❝❞❮❯⹂〝〞〟＂") | \
      set(f"\u002E\u0964\u0589\u3002\u06d4\u2cf9\u0701\u1362\u166e\u1803\u2cfe\uA4ff\ua60e\ua6f3\u083d\u1b5f\u002c\u060c\u3001\u055d\u07f8\u1363\u1808\u14fe\ua60d\ua6f5\u1b5e\u003f\u037e\u00bf\u061f\u055e\u0706\u1367\u2cfa\u2cfb\ua60f\u16f7\U00011143\uaaf1\u0021\u00a1\u07f9\u1944\u00b7\U0001039f\U000103d0\U00012470\u1361\u1680\U0001091f\u0830\u2014\u2013\u2012\u2010\u2043\ufe63\uff0d\u058a\u1806\u003b\u0387\u061b\u1364\u16f6\u2024\u003a\u1365\ua6f4\u1b5d\u2026\ufe19\u0eaf\u00ab\u2039\u00bb\u203a\u201e\u201a\u201c\u201f\u2018\u201b\u201d\u2019\u0022") | \
      set(map(chr, chain(range(0x2010, 0x2028), range(0x2030, 0x205F)))) | \
      set(map(chr, range(0x2E00, 0x2E50)))
   
   print(list(sorted(list(punctuation))))

   punctuationMapping = str.maketrans({key: " " for key in punctuation})

   with open("map_punctuationMapping.pkl", "wb") as mapping_out:
      pickle.dump(punctuationMapping, mapping_out)

#############################################
# ASCII, Hiragana, katakana and kanji only. #
#############################################

# Since this is very exclusionary, it's actually easier to list only the things
# we will keep and exclude the complement using a regex in fuzzy_match.py.
# Keep this for posterity.
# try:
#    with open("_map_emojiOtherSymbolsMapping.pkl", "rb") as mapping_in:
#       emojiOtherSymbolsMapping = pickle.load(mapping_in)
# except FileNotFoundError:
#    chain(
#       map(
#          chr,
#          chain(
#             range(0x2E80, 0x2FD5) # Kanji radicals.
#             range(0x31F0, 0x31FF), # From Miscellaneous Japanese Symbols and Characters.
#             range(0x3220, 0x3243), # Ibid.
#             range(0x3280, 0x337F), # Ibid.
#             range(0x3021, 0x3030), # From CJK Symbols and Punctuation.
#             range(0x3036, 0x303B) # Ibid.
#          )
#       ),
#       ["〄", "〒", "〓", "〠"], # Ibid.
#       ...???
#    )
# 
#    with open("map_emojiOtherSymbolsMapping.pkl", "wb") as mapping_out:
#       pickle.dump(emojiOtherSymbolsMapping, mapping_out)
