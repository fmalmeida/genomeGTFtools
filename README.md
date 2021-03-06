# genomeGTFtools

## Overview
These are some scripts to convert various features and annotations into a GFF-like file for use in genome browsers. There are also general purpose tools for genome annotation.

Many of these tools were used in [our analysis of the genome of the sponge *Tethya wilhelma*](https://bitbucket.org/molpalmuc/sponge-oxygen). Please cite the paper: [Mills, DB. et al (2018) The last common ancestor of animals lacked the HIF pathway and respired in low-oxygen environments. *eLife* 7:e31176.](https://doi.org/10.7554/eLife.31176)

### Jump to: ###
* [blast2gff.py](https://github.com/wrf/genomeGTFtools#blast2gff) blast hits to GFF, generally indicating exons or conserved domains
* [microsynteny.py](https://github.com/wrf/genomeGTFtools#microsynteny) using two GFF files of two different genomes and blast hits, determine blocks of conserved gene order

## number_contigs_by_length
By convention, the longest chromosomes are numbered first. This naturally applies to scaffolds as well. Contigs/scaffolds can be renumbered and reordered with `number_contigs_by_length.py` script. Use the option `-c` to specify an additional output file of the conversion vector, that can be used to rename the scaffold column in any GFF file with the `rename_gtf_contigs.py` script.

## pfam2gff
This has two modes: one will convert the "tabular" hmmscan output (generated using PFAM-A, which can be found in [the FTP section of PFAM](http://pfam.xfam.org/) as the database) into a protein GFF with domains at the protein positions. 

  `hmmscan --cpu 4 --domtblout stringtie.pfam.tab ~/PfamScan/data/Pfam-A.hmm stringtie_transdecoder_prots.fasta > stringtie.pfam.log`

  `pfam2gff.py -i stringtie.pfam.tab > stringtie.pfam.gff`

### For genomic coordinates ###
The other output will convert the domain positions into genomic coordinates for use in genome browsers, so individual domains can be viewed spanning exons. Run `hmmscan` as above, then use the `-g` option to include genomic coordinates. Use `-T` for presets for [TransDecoder genome GFF](https://github.com/TransDecoder/TransDecoder/wiki) file.

  `pfam2gff.py -g stringtie_transdecoder.gff -i stringtie.pfam.tab -T > stringtie_transdecoder_pfam_domains.gff`

## pfamgff2clans
Convert a PFAM protein GFF (above) to the PFAM clans, and remove some redundant hits, essentially just changing the names of the domains and merging duplicates. This is needed for the `pfampipeline.py` script. This script requires the [clan links file, called Pfam-A.clans.tsv](http://pfam.xfam.org/).

**BioPython is required for this step, to get the length of each sequence.**

## pfampipeline
**Requires BioPython, HMMER, PFAM-A and SignalP**
Script to generate graph of domains for a FASTA file of proteins. Both of the above scripts (`pfam2gff.py` and `pfamgff2clans.py`) are automatically called, followed by [SignalP](http://www.cbs.dtu.dk/services/SignalP/) and the R script `draw_protein_gtf.R`. This is called as a command on a protein file, for example on the test dataset of [nidogen](http://www.uniprot.org/uniprot/P14543) proteins:

`pfampipeline.py test_data/nidogen_full_prots.fasta`

Several output files are automatically generated, including the domain assignments in a GFF-like format, and a PDF of the domains, where a black line indicates the protein length, black box is the signal peptide, and colors correspond to different domains. **Note that some domains may overlap, due to bad calls in the HMM. Domains are by definition non-overlapping, thus these must be removed. Automatic removal may be implemented in the future.**

![nidogen_full_prots.png](https://github.com/wrf/genomeGTFtools/blob/master/test_data/nidogen_full_prots.png)

To view exon structure from a GFF file on a 3D protein structure, see instructions at my [PDBcolor repo](https://github.com/wrf/pdbcolor#gene-structure).

## repeat2gtf
From scaffolds or masked contigs, generate a feature for each long repeat of N's or n's (or any other arbitrary letter or pattern). The most obvious application is to make a track for gaps, which is the default behavior. The search is a regular expression, so could be any other simple repeat as well - CACA, CAG (glutamine repeats).

  `repeat2gtf.py scaffolds.fasta > scaffolds_gaps.gtf`

## pal2gtf
Convert palindromic repeats from the [EMBOSS program palindrome](http://emboss.sourceforge.net/apps/release/6.6/emboss/apps/palindrome.html) into GTF features. This was meant for mitochondrial genomes, but could potentially be whole nuclear genomes.

## blast2gff
This was a strategy to convert blast hits into gene models. The direction of the blast hit and the grouping of blast hits in the same region is most indicative of a gene (though possibly pseudogenes as well). In general, blasting all human proteins against the target genome can find many proteins even in distantly related organisms. Repeated domains or very common domains (like ATP binding for kinases) will show up all over the place, so limiting the `-max_target_seqs` is advisable.

1) Blast a protein set against the genome, and make use of the multithreading power of blast.

  `tblastn -query proteins.fa -db target_genome.fa -num_threads 16 -outfmt 6 > prots_vs_genome.tab`

2) Run blast2gff.py on the output file. This will reformat the tabular blast hits into gff3 alignment style. Simple filtering options can be applied with `-e` `-s` and `-F`. If the queries were from SwissProt, use the `-S` option to correctly format the SwissProt fasta headers for the output.

  `blast2gff.py -b prots_vs_genome.tab > prots_vs_genome.gff3`

## blast2genomegff
As above for the domains in `pfam2gff.py`, entire blast hits to transcripts or proteins can be printed as GFF using the `blast2genomegff.py` script, where the blast hits will be shown spanning multiple exons as a single feature. This might help to identify erroneously fused genes. Using transcripts from a *de novo* transcriptome [Trinity](http://trinityrnaseq.github.io/), or genome guided [StringTie](http://ccb.jhu.edu/software/stringtie/), convert blastx protein matches into genomic coordinates.

1) Blastx the transcriptome against a protein set, such as [Swissprot](https://www.uniprot.org/downloads), or perhaps gene models of a related organism.

  `blastx -query transcripts.fasta -db uniprot_sprot.fasta -num_threads 16 -outfmt 6 -max_target_seqs 5 > transcripts_sprot.tab`
  
2) Convert to genomic coordinates, so individual protein hits can be seen spanning exons. Transcripts from StringTie can be used directly. For Trinity transcripts, the coordinates on the genome need to be determined by mapping the transcripts to the genome. This can be done with [GMAP](http://research-pub.gene.com/gmap/).

  `blast2genomegff.py -b transcripts_sprot.tab -d uniprot_sprot.fasta -g transcripts.gtf > transcripts_sprot.genome.gff`

## microsynteny
Blocks of colinear genes between two species can be identified using `blast` and GFF files of the gene positions for each species.

1) Blastx or blastp of the transcriptome (or translated CDS) against a database of proteins from the target species. Use the tabular output `-outfmt 6`. A maximum number of sequences does not need to be set, since the objective is to find homology, and this is not assumed from blast similarity. For example, here I am using the genomes of the corals [Acropora digitifera](http://marinegenomics.oist.jp/coral/viewer/info?project_id=3) and [Styllophora pistillata](http://spis.reefgenomics.org/).

  `blastp -query adi_aug101220_pasa_prot.fa -db Spis.genome.annotation.pep.longest.fa -outfmt 6 -evalue 1e-2 > acropora_vs_styllophora_blastp.tab`

2) Determine the blocks with the `microsynteny.py` script. Various delimiter parameters may need to be set depending on the version of GFF for the annotations and the names of the proteins. In this case, as the subject proteins contain the same names as the `ID` field in the GFF, the delimiter `-D` must be set to any alternate symbol, here using `|`.

  `microsynteny.py -b acropora_vs_styllophora_blastp.tab -q test_data/adi_aug101220_pasa_mrna_t1_only.gff -d test_data/Spis.genome.annotation.mrna_only.gff -D "|" > test_data/acropora_vs_styllophora_microsynteny.tab`

The standard output is a tab-delimited text file of 11 columns. The colinear block is evident from the systematic numbering of the two genomes, as the five *A. digitifera* genes (numbered 23536-23540) correspond to the five *S. pistillata* genes (Spis14158-14162). The strand direction is the same for each gene as well.

```
query-scaf	sub-scaf	block-id	query-gene	q-start	q-end	q-strand	sub-gene	s-start	s-end	s-strand
scaf16952	Spis.scaffold280|size416857	blk-2	aug_v2a.23536.t1	23026	25506	+	Spis14158	255619	257861	+
scaf16952	Spis.scaffold280|size416857	blk-2	aug_v2a.23537.t1	28396	43517	+	Spis14159	264153	287169	+
scaf16952	Spis.scaffold280|size416857	blk-2	aug_v2a.23538.t1	53236	67680	+	Spis14160	294209	310911	+
scaf16952	Spis.scaffold280|size416857	blk-2	aug_v2a.23539.t1	68035	73535	-	Spis14161	321061	322080	-
scaf16952	Spis.scaffold280|size416857	blk-2	aug_v2a.23540.t1	77256	88420	+	Spis14162	340030	347635	+
```

There are two main caveats to the data generated by this program. First, the reported block length represents the most genes on *either query or target* scaffolds, meaning if genes are erronously fused or split on one of the two species, this could, for instance, generate a block of 1 gene in the query and 3 genes in the target. Below is an example of a block where gene `aug_v2a.19447.t1` blasts to five genes in a row in *S. pistillata*. From these data alone, it cannot be determined if the *A. digitifera* gene is a false fusion, or the *S. pistillata* genes are falsely split.

```
scaf11463	Spis.scaffold21|size1341190	blk-19	aug_v2a.19446.t1	188491	189125	-	Spis2568	665897	666978	-
scaf11463	Spis.scaffold21|size1341190	blk-19	aug_v2a.19447.t1	192487	193775	-	Spis2569	668955	676058	-
scaf11463	Spis.scaffold21|size1341190	blk-19	aug_v2a.19447.t1	192487	193775	-	Spis2573.t2	740727	760040	-
scaf11463	Spis.scaffold21|size1341190	blk-19	aug_v2a.19447.t1	192487	193775	-	Spis2572	715149	725680	-
scaf11463	Spis.scaffold21|size1341190	blk-19	aug_v2a.19447.t1	192487	193775	-	Spis2571	705673	706617	-
scaf11463	Spis.scaffold21|size1341190	blk-19	aug_v2a.19447.t1	192487	193775	-	Spis2575	784361	787164	-
```

The other potential problem occurs in the case of tandem duplications. If a tandem duplication occurred in one of the two genomes, then nearly identical blocks will be identified for each duplicate, as up to 5 intervening genes are allowed (by the option `-s`). A hypothetical example is shown in the figure below. In such a case, hypothetical genes 1-3 would be matched twice (once normally, once with the intervening gene 1b), meaning the block will be counted twice.

![microsynteny_example_v1.png](https://github.com/wrf/genomeGTFtools/blob/master/test_data/microsynteny_example_v1.png)

3) Optionally, determine the frequency of random matches using the `-R` option. This will randomly reorder the positions of the query proteins, and then check for synteny. Blocks of 3-in-a-row are extremely rare, though blocks of two can be found easily by setting `-m 2`. This suggests that 3 colinear genes is usually sufficient to infer inherited gene order between the two species. Usually, long blocks are actually erroneous gene fusions in one of the genomes (as above).

  `microsynteny.py -b acropora_vs_styllophora_blastp.tab -q test_data/adi_aug101220_pasa_mrna_t1_only.gff -d test_data/Spis.genome.annotation.mrna_only.gff -D "|" -R -m 2 > test_data/acropora_vs_styllophora_microsynteny.randomized.tab`

4) A summary plot of block lengths can be produced using the associated R script `synteny_block_length_plot.R`.

  `Rscript synteny_block_length_plot.R acropora_vs_styllophora_microsynteny.tab`

![acropora_vs_styllophora_microsynteny.png](https://github.com/wrf/genomeGTFtools/blob/master/test_data/acropora_vs_styllophora_microsynteny.png)

## DEPRICATED: blast2genewise
**To get gene models from blast hits, the best strategy may be to use** `blast2gff.py` **with the option** `-A` **to convert the blast hits to** [AUGUSTUS hints](http://augustus.gobics.de/binaries/README.TXT) (which are in a GFF-like format). This is then specified in the [AUGUSTUS](http://bioinf.uni-greifswald.de/augustus/) run as: `--hintsfile=geneset_vs_scaffolds.gff`

  `blast2gff.py -t CDSpart -b geneset_vs_scaffolds.tab -A > geneset_vs_scaffolds.gff`

The original idea was intended to take advantage of the speed of blasting. Blast hits are then parsed to give a single command to [Genewise](http://dendrome.ucdavis.edu/resources/tooldocs/wise2/doc_wise2.html), and the gff output is collected into a single file and reformatted for modern genome browsers. This is very similar to the strategy used by the [BUSCO pipeline](https://gitlab.com/ezlab/busco), which takes blast hits and runs AUGUSTUS on the scaffold that was hit. As AUGUSTUS can use HMM-like profiles to find specific proteins that are conserved, perhaps with more complex domain structures, this might be developed further.

