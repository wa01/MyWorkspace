#!/usr/bin/env python
import re,os
import ROOT
from sys import argv, stdout, stderr, exit
from optparse import OptionParser
from HiggsAnalysis.CombinedLimit.DatacardParser import *
from cardFileWriter import cardFileWriter

class Result:

    def __init__(self,fname=None):
        self.obs = None
        self.exp = None

        if fname!=None:
            f = ROOT.TFile(fname)
            t = f.Get("limit")
            l = t.GetLeaf("limit")
            qE = t.GetLeaf("quantileExpected")
            for i in range(t.GetEntries()):
                t.GetEntry(i)
                q = qE.GetValue()
                if q<0.:
                    assert self.obs==None
                    self.obs = l.GetValue()
                elif abs(q-0.5)<0.001:
                    assert self.exp==None
                    self.exp = l.GetValue()

            
def getLimit(fname):
    if os.path.exists(rootFile):
        os.remove(rootFile)
    status = os.system("combine -M Asymptotic "+fname)
    if status!=0 or not os.path.exists(rootFile):
        return Result()
    return Result(rootFile)

def printLimit(b,r):
    line = "{0:10s}".format(b)
    if r.obs!=None:
        line += "{0:15.2f}".format(r.obs)
    else:
        line += "{0:>13s}  ".format("-")
    if r.exp!=None:
        line += "{0:15.2f}".format(r.exp)
    else:
        line += "{0:>13s}  ".format("-")
    print line
        
dcparser = OptionParser()
addDatacardParserOptions(dcparser)
(dcoptions, dcargs) = dcparser.parse_args([])
dc = parseCard(file(argv[1]),dcoptions)

sigBins = [ ]
for b in dc.bins:
    if b.endswith("S") and b[:2]>="J5":
        assert not b in sigBins
        sigBins.append(b)

cardsFile = "tmp.txt"
rootFile = "higgsCombineTest.Asymptotic.mH120.root"

fullResult = getLimit(argv[1])

allResults = { }
for b in sigBins:
    print "Trying bin ",b
    if os.path.exists(cardsFile):
        os.remove(cardsFile)
    status = os.system("python selectRegions.py "+argv[1]+" "+b)
    if status!=0 or not os.path.exists(cardsFile):
        break
        continue

    allResults[b] = getLimit(cardsFile)


printLimit("All",fullResult)
for b in sorted(allResults.keys()):
    printLimit(b,allResults[b])
