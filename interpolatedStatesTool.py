#!/usr/bin/env python
# encoding: utf-8

__version__ = "0.2"

import vanilla
import time, math
from AppKit import NSBeep

""" Interpolated states.
    
    Should be a simple tool to use: interpolate between non-breaking point moves.
        Small window with a "save state" button that records a mathglyph of the current glyph.
        When 1 or more states have been recorded the slider then interpolates between them.
        The last state before the slider is used is the 100% state, this one does not need to be added explicitly.
        
    The tool should not try to do too much compatibility checking.
    
"""

from robofab.pens.digestPen import DigestPointPen
from fontMath.mathGlyph import MathGlyph

class GlyphState(object):
    def __init__(self, glyph, soft=False):
        p = DigestPointPen(ignoreSmoothAndName=True)
        glyph.drawPoints(p)
        self.digest = p.getDigest()
        self.glyph = MathGlyph(glyph)
        self.t = time.time()
        self.name = glyph.name
        self.soft = soft
    
    def breakCycles(self):
        # not sure if we need to be so explicit
        # but it will happen a lot, so might as well be safe.
        self.glyph = None
        self.digest = None
        
    def __repr__(self):
        return "<GlyphState for %s %3.3f>"%(self.name, self.t)
    
    def getDigest(self):
        return self.digest
        
    def getGlyph(self):
        return self.glyph
    
class InterpolatedStateTool(object):
    def __init__(self):
        self._states = []
        self._lastState = None    # place for the last state before we start interpolating
        self._lastName = ""
        self._currentGlyph = None
        self.w = vanilla.Window((300, 90), "Interpolated State %s"%__version__)
        self.w.saveButton = vanilla.Button((5, 5, -35, 20), "Add State", callback=self.callbackSaveButton)
        self.w.clearButton = vanilla.Button((-30, 5, -5, 20), u"✕", callback=self.callbackClearButton)
        self.w.interpolateSlider = vanilla.Slider((5, 35, -5, 20), 0, 100, 100, callback=self.callbackInterpolateSlider)
        self.w.interpolateSlider.enable(False)
        self.w.status = vanilla.TextBox((5,-25, -5, 20), "", sizeStyle="mini")

        self.w.bind("close", self.bindingWindowClosed)
        self.w.bind("became main", self.bindingWindowBecameMain)
        self.reportStatus("Add a glyph.")
        self.w.open()
        
    def reportStatus(self, text=None):
        if text is None:
            l = len(self._states)
            plural = ""
            if l == 0 or l > 1:
                plural = "s"
            self.w.status.set("%d state%s recorded"%(l, plural))
        else:
            self.w.status.set(text)
    
    def bindingWindowClosed(self, sender):
        for item in self._sates:
            item.breakCycles()
    
    def bindingWindowBecameMain(self, sender):
        self._currentGlyph = g = CurrentGlyph()
        if g is None:
            self._lastState = None
            self._lastName = ""
        else:
            s = GlyphState(g, soft=True)
            if len(self._states)>1:
                
                if self._states[-1].digest != s.digest:
                   if self._states[-1].soft:
                       self._states = self._states[:-1]
                       self._states.append(s)
                   else:
                       self._states.append(s)
                    
            self._lastState = s
            self._lastName = g.name

        self.enableButtons()
    
    def enableButtons(self):
        if self._lastState is None:
            self.w.saveButton.enable(False)
            self.w.saveButton.setTitle("No glyph")
        else:
            self.w.saveButton.enable(True)
            self.w.saveButton.setTitle("Add %s"%self._lastName)
            
        if len(self._states)==0:
            self.w.clearButton.enable(False)
        else:
            self.w.clearButton.enable(True)
    
    def saveState(self):
        try:
            if self._currentGlyph is None:
                return    
            state = GlyphState(self._currentGlyph)
            if len(self._states)>0:
                if state.digest == self._states[-1].digest:
                    self.reportStatus("Already got this one.")
                    NSBeep()
                    return
            self.reportStatus("This is a new one.")
            self._states.append(state)
            self.w.clearButton.enable(True)
            self.reportStatus()
            if len(self._states)>0:
                self.w.interpolateSlider.enable(True)
            else:
                self.w.interpolateSlider.enable(False)
        except:
            import traceback
            print traceback.format_exc(5)
            self._lastState = None
            self.w.interpolateSlider.enable(False)
            self.w.clearButton.enable(False)
            self.w.saveButton.enable(False)
        
    def callbackSaveButton(self, sender):
        print sender
        self.saveState()

    def callbackClearButton(self, sender):
        self._states = []
        self.reportStatus()
        self.w.clearButton.enable(False)
        self.w.interpolateSlider.enable(False)
        self.reportStatus("Add a glyph.")
    
    def _interpolate(self, a, b, factor):
        r = a + factor*(b-a)
        return True, r
        
    def callbackInterpolateSlider(self, sender):
        """ This interpolates between all the states in sequence. 
            The last state before we started sliding is the 100%
                                    
            o--------o--------o--------o--------o    state list
            |        |        |        |        |
            first    2        3        4        current

            |                                   |            
            |............^.......................    slider
            |            |                      |
            0            f                      1    factor
            
            """
        stateCount = len(self._states)
        factor = sender.get()*0.01
        final = None
        length = len(self._states)-1

        ok = False
        if stateCount==1:
            a = self._states[0].getGlyph()
            b = self._lastState.getGlyph()
            ok, final = self._interpolate(a, b, factor)
        else:

            if factor == 0:
                # get the oldest
                final = self._states[0].getGlyph()
                ok = True
            elif factor == 1:
                # get the newest
                final = self._states[-1].getGlyph()
                ok = True
            else:
                prevIdx = int(math.floor(length*factor))
                nextIdx = prevIdx+1
                m1 = prevIdx/float(length)
                m2 = nextIdx/float(length)

                a = self._states[prevIdx].getGlyph()
                b = self._states[nextIdx].getGlyph()
                relativeFactor = (factor-m1)/ (m2-m1)

                ok, final = self._interpolate(a, b, relativeFactor)
        if not ok:
            return False
        # Now we need to apply the resulting mathglyph to the glyph in the window.
        # Note: we're actually drawing in the currentglyph. Undo will be affected.
        final.extractGlyph(self._currentGlyph)            
    
if __name__ == "__main__":
    ist = InterpolatedStateTool()