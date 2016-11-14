#
# summarize uncertainties and correlations from a datacard file
#
BEGIN{
    nb = 0;
    np = 0;
    rates = 0;
    titleWidth = 30;
}
/^bin/{
    nbl += 1;
    if(nb==0) {
	# found (first) line with bin names
	nb=NF-1;
	# print line with bin names
	line = substr($0,0,titleWidth);
	for(i=0;i<nb;i++){
	    b[i] = $(i+2);
	    line = line " ";
	    line = line b[i] "";
	}
	print line;
    }
    else if (np==0) {
	# found line with bin x process names
	np=(NF-1)/nb;
    }
    next;
}
/^rate/{
    # found line with rates
    rates = 1;
    next;
}
{
    # uncertainties: only process lines after "rates"
    # check #fields
    if (rates==1 && ( NF==(np*nb+2) || ( $2=="gmN" && NF==(np*nb+3) ) ) ) {
	# start output line
	line = substr($0,0,titleWidth);
	# loop over bins
	for (i=0;i<nb;++i) {
	    line = line "   ";
	    # loop over processes
	    for (j=0;j<np;++j) {
		# calculate field # (+1 if gmN uncertainty)
		n = np*i + j + 3;
		if ( $2=="gmN" )  n += 1;
		f = $n;
		# if present mark bin with "x" (otherwise "-")
		if (f!="-") {
		    line = line "x";
		}
		else {
		    line = line "-";
		}
	    }
	    line = line "  ";
	}
	print line;
    }
}
