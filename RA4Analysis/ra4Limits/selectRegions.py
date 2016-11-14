#!/usr/bin/env python
import re
from sys import argv, stdout, stderr, exit
from optparse import OptionParser
from HiggsAnalysis.CombinedLimit.DatacardParser import *
from cardFileWriter import cardFileWriter

parser = OptionParser(usage="usage: %prog [options] in.root  \nrun with --help to get list of options")
(options, args) = parser.parse_args()
if len(args) == 0:
    parser.print_usage()
    exit(1)

dcparser = OptionParser()
addDatacardParserOptions(dcparser)
(dcoptions, dcargs) = dcparser.parse_args([])
dc = parseCard(file(args[0]),dcoptions)
rateParms = { }


#
# get all related regions from list of rate params
#
allRegs = args[1].split(",")
idxReg = len(allRegs)

allPars = [ ]
idxPar = len(allPars)

while True:
    for r in dc.rateParams:
        assert len(dc.rateParams[r])==1
        assert len(dc.rateParams[r][0])==2
        for reg in allRegs:
            #
            # if region related to the parameter matches one of the
            # (implicitly or explicitly) requested ones: add all related
            # rate parameters to the list
            # 
            if r.startswith(reg+"AND"):
                # rate parameter for this line
                if not ( dc.rateParams[r][0][0][0] in allPars ):
                    allPars.append(dc.rateParams[r][0][0][0])
                # rate parameters in arguments (if any)
                if dc.rateParams[r][0][0][1].find("@")>=0:
                    for rpa in dc.rateParams[r][0][0][2].split(","):
                        if not ( rpa in allPars ):
                            allPars.append(rpa)
        if dc.rateParams[r][0][0][0] in allPars:
            #
            # if current rate parameter has been referred to: add
            # region and all rate parameters used as arguments to the lists
            # 
            idand = r.find("AND")
            assert idand>=0
            reg = r[:idand]
            if not ( reg in allRegs ):
                allRegs.append(reg)
            if dc.rateParams[r][0][0][1].find("@")>=0:
                for rpa in dc.rateParams[r][0][0][2].split(","):
                    if not ( rpa in allPars ):
                        allPars.append(rpa)
    if idxReg==len(allRegs) and idxPar==len(allPars):
        break
    idxReg = len(allRegs)
    idxPar = len(allPars)
    
allRegs.sort()
allPars.sort()
print " "
print "Regs:",allRegs
print "Pars:",allPars

#
# Start to build new card file
#
cfw = cardFileWriter()
cfw.defWidth = 15
cfw.maxUncNameWidth = 20
cfw.maxUncStrWidth = 10
cfw.precision = 6

#
# enter selected bins (all processes)
#
for b in dc.bins:
    if b in allRegs:
        cfw.addBin(b,[p for p in dc.processes if p!="signal"],b)
        cfw.specifyObservation(b,int(dc.obs[b]+0.5))
        for p in dc.processes:
            cfw.specifyExpectation(b,p,dc.exp[b][p])
#
# enter systematics (exclude (rate) parameters)
#
for syst in dc.systs:
    if syst[2]=="param":
        continue
    if syst[2]=="gmN":
        n = syst[3][0]
    else:
        n = 0
    # check for at least one non-zero entry
    skip = True
    for b in syst[4]:
        if not b in allRegs:
            continue
        assert b in dc.bins
        for p,v in syst[4][b].iteritems():
            assert p in dc.processes
            if v!=0.0:
                skip = False
                break
        if not skip:
            break
    if skip:
        continue
    # now add uncertainty and specify the values / bin / process
    cfw.addUncertainty(syst[0],syst[2],n)
    for b in syst[4]:
        if not b in allRegs:
            continue
        assert b in dc.bins
        for p,v in syst[4][b].iteritems():
            assert p in dc.processes
            if v!=0.0:
                cfw.specifyUncertainty(syst[0],b,p,v)
#
# add (rate) parameters by directly copying the lines
#
for l in open(args[0]):
    if l.startswith("#"):
        continue
    fields = l[:-1].split()
    if len(fields)<2 or ( fields[1]!="rateParam" and fields[1]!="param" ):
        continue
    if fields[0] in allPars:
        cfw.addExtraLine(l[:-1])

cfw.writeToFile("tmp.txt")
