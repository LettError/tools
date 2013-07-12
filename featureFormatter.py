#!/usr/bin/env python
# encoding: utf-8

import sys
import os
from time import strftime, localtime

"""
    A low level, non error checking formatter for .feature code text.
    See the test() at the end for a demo.
    
    This is:
        Standardised way of generating features.
        Increases legibility of the code that actually does the work. 
        
    This is not:
        An autimagic feature generator.
        
    Erik van Blokland

"""
class FeatureFormatter(object):
    """
    
        FeatureFormatter object
        
            dirName                 the dir to write the .fea in
            featurePrefix="AT"      the name pattern will be "feature_<prefix>_<liga abbreviations>(or)<your own>.fea"     
            startIndent=1           the indent to start with
            includeTimeStamp=True   True will include a readable timestamp. Nicer to read, but will confuse svn. 
            indentSpace=" "*4       whitespace filler of choice
            verbose=False           True will print a couple of things more.

    """
    def __init__(self,
            dirName,
            featurePrefix="AT",     
            startIndent=1,
            includeTimeStamp=True,
            indentSpace=" "*4,
            verbose=False,
            ):
        self.dirName = dirName
        self.verbose = verbose
        self.flags = {}     # place to store simple flags so we can check if we have written certain things.
        self.featurePrefix = featurePrefix
        self.includeTimeStamp = includeTimeStamp
        self.indentLevel = 0
        self.indentSpace = indentSpace
        self.lines = []
        self.header = []
        self.featureNames = []
        self.structure = []
        self.currentFeature = None
        self.currentLookup = None
        self.currentTableName = None
        self.indent(startIndent)
    
    def indent(self, steps=1):
        """ Increase indent level."""
        self.indentLevel += steps

    def dedent(self, steps=1):
        """ Decrease indent level."""
        self.indentLevel -= steps
        self.indentLevel = max(self.indentLevel, 0)

    def startFeature(self, name):
        """ Start a new feature, start with trailing whiteline."""
        self.addStructure("feature %s {"%name)
        self.addLine("feature %s {"%name)
        self.currentFeature = name
        self.featureNames.append(name)
        self.indent()
    
    def addStructure(self, *tags):
        for tag in tags:
            self.structure.append(self.indentLevel*self.indentSpace + tag)
    
    def endFeature(self):
        """ End the current feature. Dedent."""
        self.dedent()
        self.addLine("} %s;"%(self.currentFeature))
        self.addStructure("} %s;"%(self.currentFeature))
        self.currentFeature = None
    
    def startLookup(self, name):
        self.addStructure("lookup "+name)
        self.addLine("lookup %s {"%name)
        self.currentLookup = name
        #self.featureNames.append(name)
        self.indent()
    
    def endLookup(self):
        self.dedent()
        self.addLine("} %s;"%(self.currentLookup))
        self.currentLookup = None

    def addLine(self, *args):
        """ Add all the items to the line, at the current indent."""
        self.lines.append(self.indentLevel*self.indentSpace + " ".join(args))
    
    def comment(self, *args):
        """ Add a comment. """
        for commentLine in args:
            self.addLine("# " + str(commentLine))
        
    def title(self, *args):
        """ bigger looking comment. Titles are also added to the structure."""
        self.addStructure("'%s'"%" ".join(args))
        self.addLine()
        self.addLine()
        self.comment("-"*50)
        for a in args:
            self.comment(self.indentSpace+a)
        self.comment("-"*50)
    
    def addLastLine(self, text):
        """ Append the text to the previous line. """
        if not self.lastLineIsComment():
            self.lines[-1]+=text
        else:
            self.addLine(text)
    
    def _addSmallGroup(self, glyphNames, groupName):
        """ Format a group / sequence on a single line."""
        if groupName:
            if groupName[0]=='@':
                n = groupName[1:]
            else:
                n = groupName
            self.addLine("@%s = [ %s ]"%(n, " ".join(glyphNames)))
        else:
            self.addLine("[ %s ]"%" ".join(glyphNames))
        if groupName:
            # group definitions need a ;
            # non-group sequences might be used differently
            self.addLastLine(";")

    def addGroup(self,
            glyphNames,
            groupName=None,
            lineLength=50,
            sort=False,
            lineNumbers=True,
            comment=False
            ):
        """ Format a group or sequence. """
        # format the group nicely so that editors won't choke
        if len(glyphNames) < 5:
            self._addSmallGroup(glyphNames, groupName)
            return
        parts = glyphNames
        #self.addLine()
        if groupName:
            if groupName[0]=='@':
                n = groupName[1:]
            else:
                n = groupName
            self.addLine("@%s = ["%n)
        else:
            groupName = ""
            self.addLine("[")
        self.indent()
        self.comment("total %s names"%(len(parts)))
        if sort:
            parts.sort()
        c = 0
        lines = 0
        line = []
        # extended mode
        for n in parts:
            if c > lineLength:
                self.addLine(" ".join(line))
                line = []
                lines += 1
                c = 0
                if lines %10 == 0:
                    self.comment("line %d"%lines)
            else:
                c += len(n)+1
            line.append(n)
        if line:
            self.addLine(" ".join(line))
        self.dedent()
        if groupName:
            self.addLine("];")
        else:
            self.addLine("]")
    
    def languageSystem(self, name=None, code=None):
        """ Add a language system declaration. """
        if name == None:
            name = "DFLT"
        if code == None:
            code = "dflt"
        self.addLine("languagesystem %s %s;"%(name,code))
    
    def lookupFlag(self, *flags):
        """ Add one or more lookupflags.
            lookupflag IgnoreMarks RightToLeft; """
        self.addLine("lookupflag %s;"%(" ".join(list(flags))))
    
    def include(self, fileName):
        """ Include a filename. Check if it exists."""
        path = os.path.join(self.dirName, fileName)
        self.addLine("include(%s);"%fileName)
        if not os.path.exists(path):
            self.comment("Note: missing file at", path)
    
    def anchor(self, pos=None):
        if pos is None:
            return "<anchor NULL>"
        return "<anchor %5d %5d>"%(pos[0], pos[1])
        
    def markClass(self, glyphName, pos, className):
        """markClass aShadda_aDamma <anchor 130 404> @MARK_TOP_ACCENTS;
        """
        self.addLine("markClass %s %s %s;"%(glyphName, self.anchor(pos), className))
    
    def positionMark(self, glyphName, pos, className):
        """ define a mark class
            position mark aDamma <anchor 129 668> mark @MARK_TOP_ACCENTS;
        """
        self.addLine("position mark %s %s mark %s;"%(glyphName, self.anchor(pos), className))

    def startLigatureMarks(self, ligatureName):
        """ start the definition of a mark to ligature construct
            position ligature...
        """
        self.addLine("position ligature %s"%ligatureName)
        self.indent()

    def positionBaseMark(self, name, pos, className):
        """ definition of a mark to base
            for a single line statment
            position base aTcheheh <anchor   325  -377> mark @MARK_CLASS_BELOW;
        """
        self.addLine("position base %s "%ligatureName)
        
    def startBaseMarks(self, ligatureName, enable=True):
        """ start the definition of a mark to base construct
            for a multi-line statement.
            position base aTcheh.init
                <anchor   329  800> mark @MARK_CLASS_ABOVE
                <anchor   329  -253> mark @MARK_CLASS_BELOW;
            
        """
        if not enable:
            prefix="#"
        else:
            prefix=""
        self.addLine(prefix+"position base %s"%ligatureName)
        self.indent()
    
    def anchorBasePosition(self, pos, className, enable=True):
        """ define an anchor in a glyph, part of mark to base, or mark to ligature.
        The 'enable' flag allows the caller to write this line but comment it out.
        S
        """
        if not enable:
            prefix="#"
        else:
            prefix=""
        self.addLine(prefix+"%s mark %s"%(self.anchor(pos), className))
    
    def kern(self, firstName, secondName, value):
        self.addLine("pos %s %s <%4d 0 %4d 0>;"%(firstName, secondName, value, value))
    
    def lastLineIsComment(self):
        """ Return True if the last line is a comment. """
        if self.lines[-1].find("#")!=-1:
            print "comment?", self.lines[-1]
            return True
        return False

    def endMarks(self):
        """ Add a final semicolon, 
            If the previous line is not a comment, add it after the previous line.
            If the previous line is a comment, the semicolon would be missed.
            Then we move it to a new line.
        """
        self.dedent()
        if not self.lastLineIsComment():
            self.lines[-1]+=";"
        else:
            self.addLine(";")
    
    def ligatureFlagComponent(self):
        self.dedent()
        self.addLine("ligComponent")
        self.indent()
    
    def startTable(self, name):
        self.addLine("table %s {"%name)
        self.indent()
        self.currentTableName = name
    
    def endTable(self):
        self.dedent()
        self.addLine("} %s;"%self.currentTableName)
        self.currentTableName = None
    
    def save(self, optionalFileTitle=None):
        """Save the feature text of this feature to an external .fea file
        """
        if not optionalFileTitle:
            optionalFileTitle = "_".join(self.featureNames)
        fileName = "feature_%s_%s.fea"%(self.featurePrefix, optionalFileTitle)
        feaPath = os.path.join(self.dirName,fileName)
        if self.verbose:
            print "saving feature %s at %s"%(", ".join(self.featureNames), feaPath)
        f = open(feaPath, 'w')
        f.write(self.dump())
        f.close()
        return feaPath
    
    def dump(self):
        """ Collect all the data and make a single string. """
        text = []
        text.append("# file structure:")
        for line in self.structure:
            text.append("# %s%s"%(self.indentSpace, line))
        if self.includeTimeStamp:
            text.append("")
            text.append(strftime("# timestamp %a, %d %b %Y %H:%M:%S", localtime()))
        text+=self.lines
        return "\n".join(text)

if __name__ == "__main__":
    def test():
        """
            This shows how to use the feature formatter.
        
        """
        dirName = os.getcwd()
    
        ff = FeatureFormatter(dirName, featurePrefix="TEST")
        ff.title("Test lines for feature Formatting code.")
        ff.languageSystem()
        ff.languageSystem("arab")
        ff.languageSystem("arab", "ARA")

        # format a feature
        ff.startFeature("liga")
        ff.lookupFlag("IgnoreMarks", "RightToLeft")
        # comments will take several arguments and put each to a line.
        ff.comment("this is a comment", "this is another")
        ff.addLine("sub", "a", "by", "b;")
    
        # format a lookup within a feature
        ff.startLookup("this_is_my_lookup")
        ff.comment("this is a comment")
        ff.addLine("sub", "a", "by", "b;")
        ff.addLine("sub", "a", "by", "b;")
        ff.endLookup()
    
        # test a filename we won't be able to find
        ff.include("someOtherFile.fea")
        # test a filename we can find
        ff.include("feature_AT_liga.fea")
    
        # format a group with lots of names
        ff.comment("A very large group")
        lotsGlyphNames = ["name_%s"%i for i in range(500)]
        ff.addGroup(lotsGlyphNames, "this_is_my_group")
    
        # format a group with just a few names
        ff.comment("A group with just a few names, on a single line")
        ff.addGroup(lotsGlyphNames[:4], "this_is_my_small_group")

        # format a group with just a few names
        ff.comment("A glyphname sequence.")
        ff.addGroup(lotsGlyphNames[:4])

        ff.endFeature()
    
        ff.startFeature("mkmk")
        ff.comment("Let's check on the marks")
        ff.comment("markClass")
        ff.markClass("myGlyphName", (100, 100), "@MARKS_ABOVE")
        ff.comment("positionMark")
    
        ff.addLine()
        ff.title("mark to ligature")
        ff.startLigatureMarks("aBeh.medi_aNun.fina")
        ff.comment("original glyphname 1")
        ff.anchorBasePosition((713,503), "@MARK_TOP_ACCENTS")
        ff.anchorBasePosition((701,-296), "@MARK_BOTTOM_ACCENTS")
        ff.ligatureFlagComponent()
        ff.comment("original glyphname 2")
        ff.anchorBasePosition((313,503), "@MARK_TOP_ACCENTS")
        ff.anchorBasePosition((301,-296), "@MARK_BOTTOM_ACCENTS")
        ff.endMarks()
    
        ff.addLine()
        ff.title("mark to base")
        ff.startLookup("makeSingleMarks")
        ff.startBaseMarks("aHah.fina")
        ff.anchorBasePosition((330,465), "@MARK_TOP_ACCENTS")
        ff.anchorBasePosition((330,465), "@MARK_TOP_ACCENTS", enable=False)
        ff.anchorBasePosition((325,-377), "@MARK_BOTTOM_ACCENTS", enable=False)
        ff.endMarks()
        ff.endLookup()
    
        ff.title("mark to mark")
        ff.startLookup("ABOVE_MKMK")
        ff.positionMark("myGlyphName", (100, 100), "@MARKS_ABOVE")
        ff.endLookup()

        ff.startLookup("BELOW_MKMK")
        ff.positionMark("myGlyphName", (100, 100), "@MARKS_BELOW")
        ff.endLookup()
        ff.endFeature()
    
        ff.title("Some kerning!")
        ff.startFeature("kern")
        ff.startLookup("arabicKern")
        ff.kern("firstName", "secondName", 100)
        ff.endLookup()
        ff.endFeature()
    
        print "saved at", ff.dump()

    test()