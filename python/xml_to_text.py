#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Use BeautifulSoup to remove all XHTML tags etc. from Aozorabunko HTML files and return undecorated and cleaned text in a new file."""

import re
from pathlib import Path
from bs4 import BeautifulSoup, UnicodeDammit

dedupNewlines = re.compile(r"[\n]{2,}")

dataPath = Path("../data")
emptyFiles = []
nonAozora = []
for workPath in dataPath.iterdir():
   if workPath.is_dir():
      print(workPath)

      htmlPath = workPath / "source_text" / "index.html"

      with htmlPath.open(mode="rb") as f:
         mirepoix = UnicodeDammit(f.read(), ["shift-jis", "utf-8", "euc-jp"])
         if not mirepoix.unicode_markup:
            print("Empty HTML file " + str(htmlPath))
            emptyFiles.append(str(htmlPath))
            continue
         else:
            soup = BeautifulSoup(mirepoix.unicode_markup, "lxml")

      try:
         main_text = soup.find_all("div", attrs={"class": "main_text"})[0]
      except IndexError:
         print("Non-Aozora bunko HTML file " + str(htmlPath))
         nonAozora.append(str(htmlPath))
         continue
      else:
         for rpt in main_text(["rp", "rt"]):
            rpt.decompose()
         
         outDir = workPath / "stripped_text"
         outDir.mkdir(exist_ok=True)
         outPath = outDir / "stripped.txt"
         with outPath.open("w") as stripped:
            stripped.write(re.sub(dedupNewlines, "\n", main_text.get_text().strip()))

print("Empty files found: ", emptyFiles)
print("Non-Aozora bunko files found: ", nonAozora)