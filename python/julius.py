##!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Send sound files to Julius for transcription."""
import subprocess

# Start Julius as a server module."""
subprocess.run(
   [
      " ".join([
         "$(julius",
         "-C", "../julius/dictation-kit/main.jconf",
         "-C", "../julius/dictation-kit/am-dnn.jconf",
         "-dnnconf", "../julius/dictation-kit/julius.dnnconf","-module", "10501)"
      ])
   ]
)