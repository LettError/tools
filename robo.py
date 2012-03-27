#!/usr/bin/python

"""
    
    Python script intended for use as a command line tool.
    It is to open up files with RoboFont.
    
    Dependencies and assumptions:
        _ needs to run on OSX.
        - needs to run on a Python version that can import AppKit.
        - needs to run on a computer that has RoboFont installed.
        
    Erik van Blokland erik@letterror.com
    

"""
from AppKit import *
import os, sys
import subprocess

version = "0.1"


acceptTypes = [ '.ufo',
                '.py',
                '.RoboFontExt',
                ".otf",
                ".ttf",
                ".woff",
                ".pfa",
                ".pfb",
                ".ttx",
                ]

helpText = """Call RoboFont.app to open UFO sources, (nested) folders of UFO sources and python scripts.
    -h  print options
    -n  open each file in a new instance of RoboFont

    Accepts these filetypes:\n\t%s
    
    Version: %s
"""%("\n\t".join(acceptTypes), version)


def openWithRoboFont(path, withNewInstance=False):
    """ Open this file with RoboFont."""
    ext = os.path.splitext(os.path.basename(path))[-1].lower()
    if ext in acceptTypes:
        if withNewInstance:
            newAppInstanceFlag = "-n "
        workspace = NSWorkspace.sharedWorkspace()
        appURL = workspace.fullPathForApplication_("RoboFont")
        cmd = "open -g %s-a \"%s\" \"%s\""%(newAppInstanceFlag, appURL, path)
        popen = os.popen(cmd)
        return
    if os.path.isdir(path):
        for n in os.listdir(path):
            option = os.path.join(path, n)
            openWithRoboFont(option)
        return
    else:
        print "RoboFont can't open file %s"%os.path.splitext(path)[-1]
        return

path = None
flags = {}
paths = []
print sys.argv
for arg in sys.argv[1:]: 
    if arg[0]=='-':
        flags[arg[1:]]=True
    else:
        paths.append(arg)

withNewInstance = False
if flags.get('h'):
    print helpText
    print flags
if flags.get("n"):
    withNewInstance = True

if paths:
    for p in paths:
        openWithRoboFont(p, withNewInstance)
    
