#!/usr/local/env python3
# -*- coding: utf-8 -*-
"""Runs a Julius server for each work on a different port."""

from pathlib import Path
from subprocess import run
from multiprocessing import Pool

from call_julius import main

juliusPath = Path("../julius")
dictationKit = juliusPath / "dictation-kit"
mainJconf = (dictationKit / "main.jconf").resolve()
amDnnJconf = (dictationKit / "am-dnn.jconf").resolve()
jDnnconf = (dictationKit / "julius.dnnconf").resolve()

def makeCommand(port, filelist):
   command = [
      "julius",
      "-C", str(mainJconf),
      "-C", str(amDnnJconf),
      "-dnnconf", str(jDnnconf),
      "-module", str(port),
      "-input", "rawfile",
      "-filelist", str(filelist),
      "-quiet"
   ]

   return command

filelists = Path("./filelists").resolve()
mainArgs = []
for port, filelist in enumerate(sorted(filelists.iterdir()), 20000):
   command = makeCommand(port, str(filelist.resolve()))
   mainArgs.append((command, port, filelist.resolve()))

pool = Pool()
pool.map(main, mainArgs)
pool.close()
pool.join()
