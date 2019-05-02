#!/usr/local/env python3
# -*- coding: utf-8 -*-
"""Scrapes websites to get the relevant data."""

import json
import pickle
import requests
from time import sleep
from pathlib import Path
from subprocess import run
from bs4 import BeautifulSoup

try:
   with open("scrape_booksDicts.pkl", "rb") as sbd:
      booksDicts = pickle.load(sbd)
except FileNotFoundError:
   booksDicts = []
   for i in range(504*20):
      sleep(1)
      idUrl = f"https://librivox.org/api/feed/audiobooks/?id={i}&format=json"
      r = requests.get(idUrl)
      rJson = r.json()
      try:
         books = rJson.get("books", {})
         for book in books:
            if book.get("language", "") == "Japanese":
               bookId = book.get("id", "")
               title = book.get("title", "")
               soundFile = book.get("url_zip_file", "")
               textFile = book.get("url_text_source", "")
               time = book.get("totaltime", "")
               reader = book.get("reader", "")
               librivox = book.get("url_librivox", "")

               authors = book.get("authors", [])
               authIdList = []
               authList = []
               for author in authors:
                  authIdList.append(author.get("id", ""))
                  authList.append(" ".join([author.get("first_name", ""), author.get("last_name", "")]))

               if not reader and librivox:
                  soup = BeautifulSoup(requests.get(librivox).content.decode("utf-8"), "lxml")
                  readBy = soup.find("dt", text="Read by:")
                  readerTag = readBy.find_next_sibling("dd")
                  reader = readerTag.a["href"]

               newDict = {
                  "id": bookId,
                  "audio": soundFile,
                  "title": title,
                  "authorIds": authIdList,
                  "authors": authList,
                  "text": textFile,
                  "reader": reader,
                  "time": time
               }
               booksDicts.append(newDict)
      except KeyError:
         continue
   with open("scrape_booksDicts.pkl", "wb") as sbd:
      pickle.dump(booksDicts, sbd)
else:
   # print(booksDicts)
   pass



multilingualWorks = [
   "https://librivox.org/librivox-multilingual-short-works-collection-001-by-various/",
   "https://librivox.org/librivox-multilingual-short-works-collection-002/",
   "https://librivox.org/librivox-multilingual-short-works-collection-003/",
   "https://librivox.org/librivox-multilingual-short-works-collection-004/",
   "https://librivox.org/librivox-multilingual-short-works-collection-005/",
   "https://librivox.org/librivox-multilingual-short-works-collection-006/",
   "https://librivox.org/librivox-multilingual-short-works-collection-007/",
   "https://librivox.org/librivox-multilingual-short-works-collection-008/",
   "https://librivox.org/multilingual-poetry-collection-001/",
   "https://librivox.org/multilingual-poetry-collection-002/",
   "https://librivox.org/multilingual-poetry-collection-003/",
   "https://librivox.org/multilingual-poetry-collection-004/",
   "https://librivox.org/multilingual-poetry-collection-005/",
   "https://librivox.org/multilingual-poetry-collection-006/",
   "https://librivox.org/multilingual-poetry-collection-007/",
   "https://librivox.org/multilingual-poetry-collection-008/",
   "https://librivox.org/multilingual-poetry-collection-vol-009/",
   "https://librivox.org/multilingual-poetry-collection-vol-010/",
   "https://librivox.org/multilingual-poetry-collection-011/",
   "https://librivox.org/multilingual-poetry-collection-volume-012/",
   "https://librivox.org/multilingual-poetry-collection-013/",
   "https://librivox.org/multilingual-poetry-collection-014/",
   "https://librivox.org/multilingual-poetry-collection-015/",
   "https://librivox.org/multilingual-poetry-collection-016-by-various/",
   "https://librivox.org/multilingual-poetry-collection-017/",
   "https://librivox.org/multilingual-poetry-collection-018/",
   "https://librivox.org/multilingual-poetry-collection-019-by-various/",
   "https://librivox.org/multilingual-poetry-collection-020-by-various/",
   "https://librivox.org/multilingual-short-story-collection-001/",
   "https://librivox.org/multilingual-short-works-collection-009-by-various/",
   "https://librivox.org/multilingual-short-works-collection-010-by-various/",
   "https://librivox.org/multilingual-short-works-collection-011-by-various/",
   "https://librivox.org/multilingual-short-works-collection-012-by-various/",
   "https://librivox.org/multilingual-short-works-collection-013-by-various/",
   "https://librivox.org/multilingual-short-works-collection-014-by-various/",
   "https://librivox.org/multilingual-short-works-collection-015/",
   "https://librivox.org/multilingual-short-works-collection-016/",
   "https://librivox.org/multilingual-short-works-collection-017-poetry-and-prose-by-various/",
   "https://librivox.org/multilingual-short-works-collection-018-poetry-prose-by-various/",
   "https://librivox.org/multilingual-short-works-collection-019-poetry-prose-by-various/",
   "https://librivox.org/multilingual-short-works-collection-020-poetry-prose-by-various/",
   "https://librivox.org/multilingual-short-works-collection-021-poetry-prose-by-various/"
]

try:
   with open("scrape_multilingDicts.pkl", "rb") as smd:
      multilingDicts = pickle.load(smd)
except FileNotFoundError:
   multilingDicts = []
   for work in multilingualWorks:
      sleep(1)
      r = requests.get(work)

      soup = BeautifulSoup(r.content.decode("utf-8"), "lxml")

      rssFeed = soup.find("dt", text="RSS Feed")
      rssTag = rssFeed.find_next_sibling("dd")
      bookId = rssTag.a["href"].split("/")[-1].strip()

      trs = soup.findAll("tr")
      for tr in trs:
         tds = tr.findAll("td")
         if not tds: continue
         if tds[-1].text == "jp":
            newDict = {
               "id": bookId,
               "audio": tds[0].findAll("a")[0]["href"],
               "title": tds[1].text,
               "authorIds": list(map(lambda link: link["href"].split("/")[-1].strip(), tds[2].findAll("a"))),
               "authors": list(map(lambda auth: auth.strip(), tds[2].text.split(","))),
               "text": tds[3].findAll("a")[0]["href"],
               "reader": tds[4].findAll("a")[0]["href"],
               "time": tds[5].text
            }
            multilingDicts.append(newDict)
   with open("scrape_multilingDicts.pkl", "wb") as smd:
      pickle.dump(multilingDicts, smd)
else:
   # print(multilingDicts)
   pass


dataPath = Path("../data/")
if not dataPath.is_dir():
   dataPath.mkdir()

# Get the relevant source text and audio for the works.
for work in multilingDicts + booksDicts:
   sleep(1)

   newWork = "_".join([work["title"]] + work["authors"]).replace(" ", "_")

   workPath = dataPath / newWork
   workPath.mkdir(exist_ok=True)

   jsonPath = workPath / "info.json"
   with jsonPath.open(mode="w") as jsonFile:
      json.dump(work, jsonFile)

   textPath = workPath / "source_text"
   textPath.mkdir(exist_ok=True)
   sourceText = textPath / "index.html"
   needsManual = []
   if not sourceText.is_file():
      with sourceText.open(mode="w", encoding="shift-jis") as st:
         try:
            r = requests.get(work["text"])
            st.write(r.content.decode("shift-jis"))
         except requests.exceptions.ConnectionError:
            print("Connection Error " + work["title"])
            needsManual.append(work)
         except requests.exceptions.MissingSchema:
            print("Missing Schema " + work["title"])
            needsManual.append(work)
         except UnicodeDecodeError:
            print("Unicode Decode Error " + work["title"])
            needsManual.append(work)
   else:
      pass

   audioPath = workPath / "source_audio"
   audioPath.mkdir(exist_ok=True)
   sourceAudio = audioPath / work["audio"].split("/")[-1]
   if not sourceAudio.is_file():
      try:
         with sourceAudio.open(mode="wb") as sa:
            try:
               r = requests.get(work["audio"])
               sa.write(r.content)
            except requests.exceptions.ConnectionError:
               print("Connection Error " + work["title"])
               needsManual.append(work)
            except requests.exceptions.MissingSchema:
               print("Missing Schema " + work["title"])
               needsManual.append(work)
      except:
         print("Audio output error " + work["title"])
         needsManual.append(work)
      else:
         if sourceAudio.suffix == ".zip":
            run(["unzip", "-qq", str(sourceAudio.resolve()), "-d", str(audioPath.resolve())])
   else:
      continue
