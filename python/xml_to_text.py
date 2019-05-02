#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Use BeautifulSoup to remove all XHTML tags etc. from Aozorabunko HTML files and return undecorated and cleaned text in a new file."""

import re
from bs4 import BeautifulSoup

filePath = "../html/kokoro_natume_souseki.html"
with open(filePath, 'r', encoding='shift_jis') as f:
   soup = BeautifulSoup(f, 'lxml')

try:
   main_text = soup.find_all("div", attrs={"class": "main_text"})[0]
except IndexError:
   pass
else:
   for rpt in main_text(["rp", "rt"]):
      rpt.decompose()
   dedupNewlines = re.compile(r"[\n]{2,}")
   with open("stripped.txt", "w") as stripped:
      stripped.write(re.sub(dedupNewlines, "\n", main_text.get_text().strip()))
