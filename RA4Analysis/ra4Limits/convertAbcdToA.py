#!/usr/bin/env python
#
# (try to) convert an "ABCD" datacard file to pure "A" datacards
# Uses some assumptions about structure and naming!!!
#
import re
import os,sys
from math import sqrt
from copy import deepcopy
from optparse import OptionParser
from HiggsAnalysis.CombinedLimit.DatacardParser import *
from cardFileWriter import cardFileWriter

parser = OptionParser()
parser.add_option("--output", "-o", dest="output", type="str", \
                      help="output file name (default=cards-AbcdToA.txt", \
                      default="cards-AbcdToA.txt")
parser.add_option("--force", "-f", dest="force", default=False, action="store_true", \
                      help="replace existing output file (default=False)")
(options, args) = parser.parse_args()
if len(args) == 0:
    parser.print_usage()
    sys.exit(1)

dcparser = OptionParser()
addDatacardParserOptions(dcparser)
(dcoptions, dcargs) = dcparser.parse_args([])
dc = parseCard(file(args[0]),dcoptions)
rateParms = { }

reRef = re.compile(r"@([0-9]+)")
def replaceParameters(rpDict):
    while True:
        replaced = False
        for rp,vals in rpDict.iteritems():
            if not type(vals)==float:
                for i in re.finditer(reRef,vals[0]):
                    j = int(i.group(1))
                    rpref = vals[1][j]
                    if rpref in rpDict:
                        vref = rpDict[rpref]
                        if type(vref)==float:
                            vals[0] = vals[0].replace(i.group(0),str(vref))
                            replaced = True
                if vals[0].find("@")<0:
                    rpDict[rp] = float(eval(vals[0]))
                    replaced = True
        if not replaced:
            break

def generateVariations(rpDict,pDict):
    pNames = sorted(pDict.keys())
    rpVarDict = { }
    for rp in rpDict.keys():
        rpVarDict[rp] = { }
        for p in [ "" ]+pNames:
            rpVarDict[rp][p] = None
    # now get central values
    allRps = deepcopy(rpDict)
    for p,vals in pDict.iteritems():
        assert not p in allRps
        allRps[p] = vals[0]
    replaceParameters(allRps)
    for rp in rpVarDict:
        rpVarDict[rp][""] = allRps[rp]
    # now vary all parameters +- 1 sigma
    rpLast = None
    pLast = None
    for i in range(len(pNames)):
        pname = pNames[i]
        rpPlusMinus = { }
        for rp in rpDict:
            rpPlusMinus[rp] = [ None, None ]
        for j in range(2):
            sgn = 2*j - 1
            allRps = deepcopy(rpDict)
            for pn,vals in pDict.iteritems():
                assert not pn in allRps
                if pn==pname:
                    allRps[pn] = vals[0]+sgn*vals[1]
                else:
                    allRps[pn] = vals[0]
            replaceParameters(allRps)
            for rp in rpPlusMinus:
                assert type(allRps[rp])==float
                rpPlusMinus[rp][j] = allRps[rp]
        for rp in rpVarDict:
            delta = (rpPlusMinus[rp][1]-rpPlusMinus[rp][0])/2.
            assert rpVarDict[rp][pname]==None
#            print delta,rpVarDict[rp][pname]
            rpVarDict[rp][pname] = delta
#            print type(delta),delta,rpVarDict[rp][pname],pname,rpVarDict[rp][pNames[0]],pNames[0]
            rpLast = rp
            pLast = pname
#        print rp,pname,rpVarDict[rp][""]
#        print " "
#    print "*",rpLast,pLast,rpVarDict[rpLast][pLast]
    #
    # now clean the dict
    #
    # print rpVarDict
    for rp in rpVarDict:
        locDel = [ ]
        for p,v in rpVarDict[rp].iteritems():
            if p=="":
                continue
            if abs(v/rpVarDict[rp][""])<1.e-3:
                locDel.append(p)
        for p in locDel:
            del rpVarDict[rp][p]
#    for rp in rpVarDict:
#        print rp,rpVarDict[rp]
    return rpVarDict
#
# identify A regions
#
aRegs = [ ]
oRegs = [ ]
for b in dc.bins:
    if int(b[1])>=5 and b.endswith("S"):
        aRegs.append(b)
    else:
        oRegs.append(b)
#
# get all rate parameters
#
allRParsByBin = { }
allRParsByRPar = { }
for par in dc.rateParams:
    bPar = None
    for b in dc.bins:
        if par.startswith(b):
            bPar = b
            break
    assert bPar!=None
    assert par.startswith(bPar+"AND")
    proc = par[len(bPar+"AND"):]
    assert proc=="W" or proc=="tt"
    if not bPar in allRParsByBin:
        allRParsByBin[bPar] = { }
    if not proc in allRParsByBin[bPar]:
        allRParsByBin[bPar][proc] = { }
    assert len(dc.rateParams[par])==1
    assert len(dc.rateParams[par][0])==2
    if "@" in dc.rateParams[par][0][0][1]:
        rpvals = [ dc.rateParams[par][0][0][1], dc.rateParams[par][0][0][2].split(",") ]
    else:
        rpvals = float(dc.rateParams[par][0][0][1])
    rp = dc.rateParams[par][0][0][0]
    assert not rp in allRParsByBin[bPar][proc]
    allRParsByBin[bPar][proc][rp] = rpvals
    assert not rp in allRParsByRPar
    allRParsByRPar[rp] = rpvals
#
# now resolve formulae with current values
#
#print allRParsByRPar["j3L1H1D2CW"]
#sys.exit(0)
replaceParameters(allRParsByRPar)
#for rp,vals in allRParsByRPar.iteritems():
#    if not type(vals)==float:
#        for i in re.finditer(reRef,vals[0]):
#            j = int(i.group(1))
#            print vals[1][j]

#
# now get all parameters
#
allParsByPar = { }
for syst in dc.systs:
    if syst[2]=="param":
        assert not syst[0] in allRParsByRPar
        assert not syst[0] in allParsByPar
        assert len(syst[3])==2
        allParsByPar[syst[0]] = [ float(x) for x in syst[3] ]
rpVarDict = generateVariations(allRParsByRPar,allParsByPar)

#
# replace rates by results from rate parameters, where necessary
#

for b in dc.bins:
    if b in allRParsByBin:
        for p in dc.processes:
            if p=="signal":
                continue
            if p in allRParsByBin[b]:
                assert len(allRParsByBin[b][p])==1
                rp = allRParsByBin[b][p].keys()[0]
                if rp.startswith("j"):
                    assert abs(dc.exp[b][p]-1.)<0.001
#                    print "Changing exp for",b,p,rp,"from",dc.exp[b][p],"to",rpVarDict[rp][""]
                    dc.exp[b][p] = rpVarDict[rp][""]

##
## cross checks
##
#for b in aRegs:
#    lb = len(b)
#    assert b.endswith("S")
#    # MB CR
#    bmbcr = b[:lb-1]+"C"
#    print bmbcr
#    assert bmbcr in oRegs
#    print bmbcr,int(dc.obs[bmbcr]+0.5),sum([dc.exp[bmbcr][p] for p in dc.processes if p!="signal"])
#    # SB W CR
#    bsbwcr = "J3"+b[2:lb-1]+"C"
#    print bsbwcr,int(dc.obs[bsbwcr]+0.5),sum([dc.exp[bsbwcr][p] for p in dc.processes if p!="signal"])
#    assert bsbwcr in oRegs
#    # SB W SR
#    bsbwsr = "J3"+b[2:lb-1]+"S"
#    print bsbwsr,int(dc.obs[bsbwsr]+0.5),sum([dc.exp[bsbwsr][p] for p in dc.processes if p!="signal"])
#    assert bsbwsr in oRegs
#    # SB tt CR
#    bsbttcr = "J4"+b[2:lb-1]+"C"
#    print bsbttcr,int(dc.obs[bsbttcr]+0.5),sum([dc.exp[bsbttcr][p] for p in dc.processes if p!="signal"])
#    assert bsbttcr in oRegs
#    # SB tt SR
#    bsbttsr = "J4"+b[2:lb-1]+"S"
#    print bsbttsr,int(dc.obs[bsbttsr]+0.5),sum([dc.exp[bsbttsr][p] for p in dc.processes if p!="signal"])
#    assert bsbttsr in oRegs

#    p = "W"
#    print "Cross check :",b,dc.exp[bsbwsr][p]/dc.exp[bsbwcr][p]*dc.exp[bmbcr][p]*allParsByPar["k"+b+p][0],dc.exp[b][p]
#    p = "tt"
#    print "Cross check :",b,dc.exp[bsbttsr][p]/dc.exp[bsbttcr][p]*dc.exp[bmbcr][p]*allParsByPar["k"+b+p][0],dc.exp[b][p]


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
    if b in aRegs:
        cfw.addBin(b,[p for p in dc.processes if p!="signal"],b)
        cfw.specifyObservation(b,int(dc.obs[b]+0.5))
        for p in dc.processes:
            cfw.specifyExpectation(b,p,dc.exp[b][p])

#
# enter systematics from input file (exclude (rate) parameters)
#
for syst in dc.systs:
    if syst[2]=="param":
        pass
    if syst[2]=="gmN":
        n = syst[3][0]
    else:
        n = 0
    # check for at least one non-zero entry
    skip = True
    for b in syst[4]:
        if not b in aRegs:
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
        if not b in aRegs:
            continue
        assert b in dc.bins
        for p,v in syst[4][b].iteritems():
            assert p in dc.processes
            if v!=0.0:
                cfw.specifyUncertainty(syst[0],b,p,v)
#
# add systematics related to yields in control regions and (rate) parameters
#
for b in oRegs:
    sname = "stat" + b
    if b.endswith("S"):
        if b.startswith("J3") or b.startswith("J4"):
            if b.startswith("J3"):
                proc = "W"
            else:
                proc = "tt"
#            print b,dc.obs[b],sum([dc.exp[b][p] for p in dc.processes if p!="signal"]),dc.exp[b][proc]
#            n = dc.obs[b]/sum([dc.exp[b][p] for p in dc.processes if p!="signal"])*dc.exp[b][proc]
            n = dc.obs[b]
            n = max(int(n+0.5),1)
            cfw.addUncertainty(sname,"gmN",n)
            for a in aRegs:
                if a[2:]==b[2:]:
                    cfw.specifyUncertainty(sname,a,proc,dc.exp[a][proc]/n)
    else:
        if b.startswith("J3") or b.startswith("J4"):
            if b.startswith("J3"):
                proc = "W"
            else:
                proc = "tt"
            pass
            sname = "stat" + b
            n = dc.obs[b]
            n = max(n,1)
            cfw.addUncertainty(sname,"lnN",n)
            for a in aRegs:
                if a[2:-1]==b[2:-1]:
                    cfw.specifyUncertainty(sname,a,proc,1+1./sqrt(n))
        else:
            a = b[:-1] + "S"
            assert a in aRegs
            sname = "stat" + b
            n = dc.obs[b]
            n = max(n,1)
            cfw.addUncertainty(sname,"lnN")
            for proc in [ "W", "tt" ]:
                cfw.specifyUncertainty(sname,a,proc,1+1./sqrt(n))
#
# add systematics related to (rate) parameters
#
# resort rpVarDict in order to get list of nuisances and related rel. variations / bin
revRpVarDict = { }
for rp in rpVarDict:
    bin = None
    proc = None
    for a in aRegs:
        if rp.upper().startswith(a):
            bin = a
            proc = rp.upper()[len(a):]
            if proc=="TT":
                proc = "tt"
            break
    if bin==None:
        continue
    for nuis,var in rpVarDict[rp].iteritems():
        if nuis=="":
            continue
        if not nuis in revRpVarDict:
            revRpVarDict[nuis] = {}
        revRpVarDict[nuis][(bin,proc)] = var/rpVarDict[rp][""]
# create systematics
for nuis in revRpVarDict.keys():
    cfw.addUncertainty(nuis,"lnN")
    for b,p in revRpVarDict[nuis]:
        cfw.specifyUncertainty(nuis,b,p,1+revRpVarDict[nuis][(b,p)])
        

if options.force or ( not os.path.exists(options.output) ):
    cfw.writeToFile(options.output)
else:
    print "Output file",options.output,"exists"
