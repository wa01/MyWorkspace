BEGIN{
    nb = 0;
    rates = 0;
}
/^bin/{
    if(nb==0) {
	nb=NF-1;
	line = substr($0,0,30);
	for(i=0;i<nb;i++){
	    b[i] = $(i+2);
	    line = line " ";
	    line = line b[i] "";
	}
	print line;
    }
    next;
}
/^rate/{
    rates = 1;
    next;
}
{
    if (rates==1 && ( NF==(5*nb+2) || ( $2=="gmN" && NF==(5*nb+3) ) ) ) {
	line = substr($0,0,30);
	for (i=0;i<nb;++i) {
	    line = line "   ";
	    for (j=0;j<5;++j) {
		n = 5*i + j + 3;
		if ( $2=="gmN" )  n += 1;
		f = $n;
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
