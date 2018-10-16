#!/usr/bin/env python

# v1.0 2014-10-22
# v1.1 added option to remove weak blast hits, fixed integer bug 2014-10-28
# v1.2 reverted to previous version after name change 2015-05-13
#
# blast2gff.py convert blast output to gff format for genome annotation
# translated from blast2gff.pl and parseblast.pl
#
# and using information from:
# https://www.sanger.ac.uk/resources/software/gff/spec.html
# http://www.sequenceontology.org/gff3.shtml

'''blast2gff.py last modified 2018-07-09

blast2gff.py -b tblastn_output.tab > output.gff3

    change the second and third fields in the gff output with -p and -t

blast2gff.py -b blastn_output.tab -p BLASTN -t EST_match > output.gff3

    tabular blast output should be made from blast programs with -outfmt 6

tblastn -query refprots.fa -db target_genome.fa -outfmt 6 > tblastn_output.tab

    evalue cutoff between 1 and 1e-3 is appropriate to filter bad hits
    though this depends on the bitscore and so the relatedness of the species

    to generate hints for AUGUSTUS, use -A, also change type as -t CDSpart
'''

#
import sys
import argparse
import time
from collections import defaultdict
#
### BLAST OUTPUTS
# default blastn or tblastn output for -outfmt 6 is printed tabular of:
#
# qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
#
# referring to: query ID, subject ID, percent identity, length of alignment,
#   mismatch count, gap openings, query start and end, subject start and end,
#   evalue, and the bitscore
#
# for example tblastn output may look:
# prot12345	Contig248	86.89	122	0	1	213	318	16668	17033	1e-63	  214
#
# where protein 12345 hit Contig248 with evalue of 1e-63
#
### GFF FORMAT
# GFF3 format is a tabular of:
#
# seqid source type start end score strand phase attributes
#
# in the context of blast results, this is converted as:
# seqid is the subject ID, so sseqid
# source is BLAST
# type could be mRNA, exon, CDS, but in this case HSP as the BLAST result
# start must always be less or equal to end, so if BLAST hits the reverse 
#   complement, these must be switched
# score is the bitscore
# strand is either + or - for forward and reverse hits
# phase is intron phase used only for "CDS" type, otherwise is "."
# attributes is a list of tag=value; pairs usually including query ID
#
#
#
# general notes:
#
# to calculate query coverage as on ncbi, appears to be query length / subject length
# to calculate identity % as on ncbi, subject length might have to be absolute value, and 1 must be added as the first base is position 1
# however on ncbi it is calculated as identities / subject length

def write_line(outlist, wayout):
	outline = "\t".join(outlist)
	print >> wayout, outline

def main(argv, wayout):
	if not len(argv):
		argv.append("-h")

	parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)
	parser.add_argument('-b','--blast', help="blast results file")
	parser.add_argument('-p','--program', help="blast program for 2nd column in output [TBLASTN]", default="TBLASTN")
	parser.add_argument('-t','--type', help="gff type or method [match_part]", default="match_part")
	parser.add_argument('-e','--evalue-cutoff', type=float, help="evalue cutoff [1]", default=1.0)
	parser.add_argument('-s','--score-cutoff', type=float, help="bitscore/length cutoff for filtering [0.1]", default=0.1)
	parser.add_argument('-A','--augustus', action="store_true", help="print source information for AUGUSTUS hints")
	parser.add_argument('-F','--filter', action="store_true", help="filter low quality matches")
	parser.add_argument('-S','--swissprot', action="store_true", help="query sequences have swissprot headers")
	parser.add_argument('-v','--verbose', action="store_true", help="extra output")
	args = parser.parse_args(argv)

	# counter for number of lines, and strand flips
	linecounter, writecounter = 0,0
	plusstrand, minusstrand = 0,0
	# counter for number of hits that are filtered
	badhits = 0

	hitDictCounter = defaultdict(int)
	print >> sys.stderr, "Starting BLAST parsing on %s" % (args.blast), time.asctime()
	for line in open(args.blast, 'r'):
		linecounter += 1
		qseqid, sseqid, pident, length, mismatch, gapopen, qstart, qend, sstart, send, slen, evalue, bitscore, stitle = line.rstrip().split("\t")

		# remove stray characters
		if args.swissprot:
		# blast outputs swissprot proteins as: sp|P0DI82|TPC2B_HUMAN
			qseqid = qseqid.split("|")[2]
		else:
			qseqid = qseqid.replace("|","")
		hitDictCounter[qseqid] += 1
		# currently 'attributes' is only query id
		# ID only appears to not work for visualization, as the gene should be the blast query
		#attributes = "ID={}".format(qseqid)
		if args.augustus:
			attributes = "source=P;ID={0}.{1}-{2}".format(sseqid, sstart, send)
		else:
			attributes = "Additional_database={1};{1}_ID={0};{1}_Target={5}".format(sseqid, args.program, hitDictCounter[qseqid], sstart, send, stitle)
		# if verbose, display the current attributes format for debugging
		if args.verbose and linecounter == 1:
			print >> sys.stderr, attributes

		# convert strings of start and end to integers for calculations
		isend = int(send)
		isstart = int(sstart)
		# as start must always be less or equal to end, reverse them for opposite strand hits
		if isstart <= isend:
			strand = "+"
			outlist = [qseqid, args.program, args.type, qstart, qend, bitscore, strand, ".", attributes]
			plusstrand += 1
		else:
			strand = "-"
			outlist = [qseqid, args.program, args.type, qend, qstart, bitscore, strand, ".", attributes]
			minusstrand += 1

		# if filtering, check if bits/length is above threshold
		if args.filter:
			fl = abs(isend-isstart)
			nbs = float(bitscore)/fl
			if nbs < args.score_cutoff:
				badhits += 1
				continue
		# check here for low evalues
		if float(evalue) > args.evalue_cutoff:
			badhits += 1
			continue
		writecounter += 1
		write_line(outlist, wayout)
	print >> sys.stderr, "Parsed %d lines" % (linecounter), time.asctime()
	print >> sys.stderr, "Found %d forward and %d reverse hits" % (plusstrand, minusstrand), time.asctime()
	if badhits:
		print >> sys.stderr, "Removed %d weak matches" % (badhits), time.asctime()
	print >> sys.stderr, "Wrote %d matches" % (writecounter), time.asctime()

if __name__ == "__main__":
	main(sys.argv[1:],sys.stdout)
