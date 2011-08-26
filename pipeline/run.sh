#!/bin/sh

# on new synteny, run these. and put .bed and .fasta files in data/ directory.
#  perl export_to_bed.pl -fasta_name rice_v6.fasta -dsg 8163 -name_re "^Os\d\dg\d{5}$" > rice_v6.bed
# perl export_to_bed.pl -fasta_name sorghum_v1.4.fasta -dsg 95 > sorghum_v1.4.bed
# perl export_to_bed.pl -fasta_name brachy_v1.fasta -dsg 8120 > brachy_v1.bed
# use OrganismView in CoGe to look up other dsgs.


ORGA=rice_v6
ORGB=sorghum_v1
QUOTA=1:1
NCPU=8

#############################################
# dont edit below here
#############################################
DIR=data/${ORGA}_${ORGB}/

echo comparing genomes, checking for unannotated proteins
#    python scripts/create_json.py \
#       --query $ORGA \
#      --subject $ORGB
####### make blast dir to home dir bin =)
#coannotate.py $DIR/${ORGA}_${ORGB}.json
#mv $DIR/${ORGA}.all.bed $DIR/${ORGA}.bed
#mv $DIR/${ORGB}.all.bed $DIR/${ORGB}.bed
echo bed files updated 
#rm $DIR/*.features*
#mkdir $DIR/mised_exons
#mv $DIR/miss* $DIR/mised_exons # ... irgnor error for mv dir
##rm *.blast
##rm  *.raw
##rm *.raw.merged
##finding syntenic regions
echo finding syntenic regions...
#sh quota.sh $DIR/${ORGA} $DIR/${ORGB} $QUOTA $NCPU
echo finding cns...
#python scripts/find_cns.py \
#        -q $DIR/${ORGA}.fasta --qbed $DIR/${ORGA}.bed \
#        -s $DIR/${ORGB}.fasta --sbed $DIR/${ORGB}.bed \
#        -p $DIR/${ORGA}_${ORGB}.pairs.txt \
#        -F T \
#        -n 8 \
#        --qpad 12000 \
#        --spad 12000 \
#        --blast_path ~/src/blast-2.2.25/bin/bl2seq \
#        --pair_fmt pair > $DIR/${ORGA}_${ORGB}.cns.txt
#
#rm -r ${ORGA}_split/ rm -r ${ORGB}_split/
#python scripts/cns_to_fasta.py \
#                -c $DIR/${ORGA}_${ORGB}.cns.txt \
#                --qfasta $DIR/${ORGA}.genomic.masked.fasta \
#                --sfasta $DIR/${ORGB}.genomic.masked.fasta \
#                --qorg ${ORGA} \
#                --sorg ${ORGB} \
#                --min_len=18 \
#                > $DIR/${ORGA}_${ORGB}.cns.fasta
echo removing cns that have hits in arabidopsis as rna or protein
#proteins_and_rna:
#### THIS is CDS/protein stuff.
#wget -O data/at_protein.fasta ftp://ftp.arabidopsis.org/home/tair/Sequences/blast_datasets/TAIR10_blastsets/TAIR10_pep_20101214
#wget -O data/os_protein.fasta ftp://ftp.plantbiology.msu.edu/pub/data/Eukaryotic_Projects/o_sativa/annotation_dbs/pseudomolecules/version_6.1/all.dir/all.p
#bblast.py -p blastx -d data/at_protein.fasta -i $DIR/${ORGA}_${ORGB}.cns.fasta -e 0.01 -m 8 -a ${NCPU} -o $DIR/at_protein.blast
#bblast.py -p blastx -d data/os_protein.fasta -i $DIR/${ORGA}_${ORGB}.cns.fasta -e 0.01 -m 8 -a ${NCPU} -o $DIR/os_protein.blast
#
#python scripts/find_exons.py \
#                 -q ${ORGA}\
#                 -s ${ORGB}\
#                 -o $DIR \
#                 $DIR/at_protein.blast $DIR/os_protein.blast
#
#NEED TO EDIT find_rna.py SO IT looks for the correct cns fasta file
#THIS IS NON-CDS
##getrna:
 # have to modify below file to be valid(er) gff3 and remove the chromosome types from teh body.
#wget -O data/thaliana_v10.gff ftp://ftp.arabidopsis.org/home/tair/Genes/TAIR10_genome_release/TAIR10_gff3/TAIR10_GFF3_genes_transposons.gff
#wget -O data/thaliana_v10.description ftp://ftp.arabidopsis.org/home/tair/Genes/TAIR10_genome_release/TAIR10_functional_descriptions
#wget -O data/thaliana_v10.fasta ftp://ftp.arabidopsis.org/home/tair/Genes/TAIR10_genome_release/TAIR9_chr_all.fas
#perl -pi -e "s/>(.).*/>\$1/" data/thaliana_v10.fasta
#
#
# #add ncpu to run.py!!!!
#python scripts/find_rna.py -g data/thaliana_v9.gff \
#         -f data/thaliana_v9.fasta \
#         -b $DIR/${ORGA}_${ORGB}_cns_vs_at_rnas.blast \
#     -q ${ORGA}  \
#       -s ${ORGB} \
#   -o $DIR \
#   -d data/thaliana_v9.description
#
#CREATE PARAPLOGY AND ORTHOLOGY WITH RAW FILTERED FILE
#shuffle_protein_cns:
  # add protein, rna cnss to the gene flat file
  # and remove them from the _cns.txt
  # this will create *.with_new.bed, _cns.real.txt, # with_new.*
#  python scripts/shuffle_protein_cns.py \
#    --qbed $DIR/${ORGA}.nolocaldups.bed \
#    --sbed $DIR/${ORGB}.nolocaldups.bed \
#    --cns  $DIR/${ORGA}_${ORGB}.cns.txt \
#    --paralogy  $DIR/${ORGA}_${ORGB}.paralogy \
#    --orthology $DIR/${ORGA}_${ORGB}.orthology \
   # creates: $DIR/${ORGA}_${ORGB}.quota.with_new.orthology
#
#python scripts/assign.py \
#      --qbed $DIR/${ORGA}.bed \
#      --sbed $DIR/${ORGB}.bed \
#      --cns $DIR/${ORGA}_${ORGB}.cns.txt \
#      --pairs $DIR/${ORGA}_${ORGB}.pairs.txt \
#      --qdsid 9109 \
#      --sdsid 95 \
#      --qpad 15000 \
#      --spad 15000 \
#      --pair_fmt pair > $DIR/${ORGA}_${ORGB}.cns.assigned.csv
#
#python scripts/cns_to_fasta.py \
#                -c $DIR/${ORGA}_${ORGB}.cns.real.txt \
#                --qfasta $DIR/${ORGA}.genomic.masked.fasta \
#                --sfasta $DIR/${ORGB}.genomic.masked.fasta \
#                --qorg ${ORGA} \
#                --sorg ${ORGB} \
#                > $DIR/${ORGA}_${ORGB}.cns_real.fasteI

echo "pipeline completed would you like to remove large and now nolonger needed files?(yes/no)"
read remove_files
if [ "$remove_files" = "yes" ]
then
	echo "yay!"
else	
	echo "no!!!!!"
fi
