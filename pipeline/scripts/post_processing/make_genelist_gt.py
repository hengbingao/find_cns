"""
('name', 'chr', other_org_name + '_orthologs',
      other_org_name + '_orthologous_cns_count',
      other_org_name +
      '_NON_orthologous_cns_count', 'other_' +
      other_org_name + 'pairs', 'dups', 'strand',
      'cds_locations', 'labels', 'link')
"""
import collections
import operator
from flatfeature import Bed
import os.path as op
import sys
sys.path.insert(0, op.dirname(__file__))
from common import parse_cns_datasheet, get_sheet_from_date, parse_orthology


def merge_flat(new_name, aflat, bflat):
    """
    take 2 flat files and return a new one that is the union of the 2 existing
    """
    seen = {}

    both = []
    for flat in (aflat, bflat):
        for row in flat:
            key = row['seqid'], row['accn']
            if key in seen: continue
            seen[key] = True
            both.append(row)
    both.sort(key=lambda a: (a['seqid'], a['start']))
    fh = open(new_name, "w")
    #print >>fh, "\t".join(Flat.names)
    for b in both:
        print >>fh, Bed.row_string(b)
    fh.close()
    return Bed(fh.name)

import datetime

def parse_pairs(pair_file, qbed, sbed):
    paired = collections.defaultdict(list)
    for line in open(pair_file):
        if line[0] =='#': continue
        line = line.split("\t")
        try:
            qseqid, qi, sseqid, si = line[:4]
        except ValueError: print >>sys.stderr, line

        q, s = qbed[int(qi)], sbed[int(si)]
        qname, sname = q['accn'], s['accn']
        
        paired[qname].append(sname)
        paired[sname].append(qname)
    new_paired = {}
    for k, v in paired.iteritems():
        new_paired[k] = sorted(list(frozenset(v)))

    return new_paired

def parse_dups(dups_file, flat):
    flat.fill_dict()
    d = {}
    for line in open(dups_file):
        all = [Bed.row_to_dict(flat.d[f]) for f in list(set([x.strip() for x in line.split("\t")]))]
        all.sort(key=operator.itemgetter('start'))
        parent = all[0]
        last_dup = all[-1]
        d[parent['accn']] = 'P'
        for a in all[1:]:
            #dups[a] = all[0]
            if not a['accn'] in d:
                d[a['accn']] = parent['accn']
        # so here, there are all the genes that arent part of the local dup
        # array, but we want to mark them with 'I'
        intervening = flat.get_features_in_region(parent['seqid'], parent['start'], last_dup['end'])
        for ii in intervening:
            if ii == parent or ii == last_dup: continue
            if not ii['accn'] in d:
                d[ii['accn']] = 'I'
    return d

def map_cns(cnss):
    """cnss are stored by an id,
    here it saves them in a dict with keys
    of accn name for both query and subject"""
    by_name = collections.defaultdict(list)
    for cns_id, info in cnss.iteritems():
        by_name[info['saccn']].append(info)
        by_name[info['qaccn']].append(info)
    return dict(by_name)



def split_cns(cnss, orthos, flip=False):
    keya, keyb = ('qaccn', 'saccn')
    if not cnss:
        return [], cnss

    ort = []
    non = []
    for cns in cnss[:]:
        #print >>sys.stderr, cns[keya], cns[keyb]
        if (cns[keya], cns[keyb]) in orthos:
            ort.append(cns)
        else:
            non.append(cns)
    assert len(ort) + len(non) == len(cnss)
    return ort, non

def split_pairs(feat, pairs, orthos, flip=False):
    ort, non = [], []
    for pair in pairs:
        key = (pair['accn'], feat['accn']) if flip \
                        else (feat['accn'], pair['accn'])

        if key in orthos:
            ort.append(pair)
        else:
            non.append(pair)

    assert len(ort) + len(non) == len(pairs)
    return ort, non


def write_genelist(q_or_s, outfile, flat, pairs, orthos, mcnss, link_fmt, this_org, other_org,
        other_flat, dups, local_dups):
    # used in the link_fmt
    qorg, sorg = this_org, other_org

    fmt = "%(accn)s\t%(seqid)s\t%(start)i\t%(end)i\t%(ortholog)s\t%(ortho_cns_count)s\t"
    fmt += "%(ortho_NON_cns_count)s\t%(other_pairs)s\t%(dup_info)s\t%(local_dup_info)\t%(strand)s\t"
    fmt += "%(new_gene_info)s\t%(link)s"
    header = fmt.replace('%(', '').replace(')s','').replace(')i','')

    outdir = op.dirname(flat.path)
    annos = dict([kv.rstrip().split(",") for kv in open("%s/%s_protein_rna.anno" % (outdir, q_or_s))])
    if flat.path == other_flat.path:
        annos.update(dict([kv.rstrip().split(",") for kv in open("%s/s_protein_rna.anno" % (outdir,))]))

    out = open(outfile, 'w')
    print >>sys.stderr, "writing genelist to %s" % (outfile,)
    print >>out, header.replace('ortho_', other_org + '_')

    same_org = this_org == other_org
    for feat in flat:

        these_pairs = pairs.get(feat['accn'], [])
        cnss = mcnss.get(feat['accn'], [])

        ortholog, other_pairs = split_pairs(feat, [other_flat.d[t] for t in these_pairs], orthos, q_or_s=='s')
        ortho_cns, non_ortho_cns = split_cns(cnss, orthos, q_or_s=='s')

        dup_info = dups.get(feat['accn'], '')
        local_dup_info = local_dups.get(feat['accn'],'')

        if ortholog:
            ortho = ortholog[0]
            link = link_fmt % dict(x1=feat['start'], chr1=feat['seqid'], qorg=qorg, sorg=sorg,
                                   x2=ortho['start'], chr2=ortho['seqid'],
                                    qseqid=feat['seqid'], qstart=feat['start'] - 10000, qstop=feat['end'] + 10000,
                                    sseqid=ortho['seqid'], sstart=ortho['start'] - 10000, sstop=ortho['end'] + 10000
                                  )
        else:
            link = ''

        new_gene_info = ""
        if feat['accn'].endswith(("_cns_protein", "_cns_rna")):
            try:
                new_gene_info = annos[feat['accn']]
            except KeyError: # from coannoation of previous run.
                pass

        ortholog = len(ortholog) and ",".join([o["accn"] for o in ortholog]) or ""
        if len(ortho_cns) > 0 and len(ortholog) == 0:
           print >>sys.stderr, "\nBAD", feat, "\n", ortho_cns, "\nthese:", these_pairs, "\nother:", other_pairs, "\n\n"
           # fell right on the edge of a syntenic block. the cns got in, but not the gene.
           #1/0

        other_pairs = ",".join([o["accn"] for o in other_pairs])
        fmt_dict = locals()
        fmt_dict.update(Bed.row_to_dict(feat))
        fmt_dict.update({'ortho_cns_count': len(ortho_cns) if ortholog else "",
                         'ortho_NON_cns_count': len(non_ortho_cns) if other_pairs else ""})
        print >>out, fmt % fmt_dict


if __name__ == "__main__":
    import optparse
    import sys
    parser = optparse.OptionParser()
    parser.add_option("--qflat_all", dest="qflat_all", help="original query flat file")
    parser.add_option("--sflat_all", dest="sflat_all", help="original subject flat file")
    parser.add_option("--qflat_new", dest="qflat_new", help="query flat file with new genes and no dups")
    parser.add_option("--sflat_new", dest="sflat_new", help="subject flat file with new genes and no dups")

    parser.add_option("--datasheet", dest="datasheet", help="cns datasheet")
    parser.add_option("--qdsid", dest="qdsid", help="query dataset_id")
    parser.add_option("--sdsid", dest="sdsid", help="subject dataset_id")
    parser.add_option("--qorg", dest="qorg", help="name of query organism")
    parser.add_option("--sorg", dest="sorg", help="name of subject organism")
    parser.add_option("--qdups",  dest="qdups",  help="query dups")
    parser.add_option("--sdups",  dest="sdups",  help="subject dups")
    parser.add_option("--qlocal", dest="qlocaldups", help="query local dups 3")
    parser.add_option("--slocal", dest="slocaldups", help="subject local dups 3")
    parser.add_option("--paralogy",  dest="paralogy",  help="paralogy file")
    parser.add_option("--orthology",  dest="orthology",  help="orthology file")

    opts, _ = parser.parse_args()

    if not (opts.qflat_all and opts.sflat_all and opts.datasheet):
        print "A"
        sys.exit(parser.print_help())
    if not (opts.qdsid and opts.qorg and opts.sorg):
        print "B"
        sys.exit(parser.print_help())
    if not (opts. qdups and opts.sdups and opts.paralogy and opts.orthology):
        print "C"
        sys.exit(parser.print_help())

    qflat_new = Bed(opts.qflat_new)
    sflat_new = qflat_new if opts.qflat_new == opts.sflat_new else Bed(opts.sflat_new)

    qflat_all = Bed(opts.qflat_all)
    sflat_all = qflat_all if opts.qflat_all == opts.sflat_all else Bed(opts.sflat_all)

    qfpath = "%s.all%s" % op.splitext(qflat_new.path)
    sfpath = "%s.all%s" % op.splitext(sflat_new.path)

    qflat = merge_flat(qfpath, qflat_all, qflat_new)
    sflat = merge_flat(sfpath, sflat_all, sflat_new)

    
    qdups = parse_dups(opts.qdups, qflat)
    sdups = parse_dups(opts.sdups, sflat)
    qlocaldups = parse_dups(opts.qdups,qflat)
    slocaldups = parse_dups(opts.sdups,sflat)

    pairs = parse_pairs(opts.paralogy, qflat_new, sflat_new)

    dpath = get_sheet_from_date(opts.datasheet)
    cns_info_by_hash = dict(parse_cns_datasheet(dpath))
    out_dir = op.dirname(dpath)


    orthos = parse_orthology(opts.orthology, qflat_new, sflat_new)

    mcns = map_cns(cns_info_by_hash)
    
    tdate = str(datetime.date.today())
    qout = op.join(out_dir, opts.qorg +
            ".genelist-" + tdate + ".csv")
    
    link = "http://coge.iplantcollaborative.org/CoGe/GEvo.pl?prog=blastn&dsid1=" + \
                  opts.qdsid + "&dsid2=" + opts.sdsid + \
                  "&x1=%(x1)s&x2=%(x2)s&chr1=%(chr1)s&chr2=%(chr2)s&num_seqs=2&autogo=1" 
    
    """link = "http://syntelog.com/gobe-demo/rr/?locs=%(qorg)s..%(qseqid)s..%(qstart)s..%(qstop)i" + \
                                                 "&locs=%(sorg)s..%(sseqid)s..%(sstart)i..%(sstop)i"
    """
    write_genelist('q', qout, qflat, pairs, orthos, mcns, link, opts.qorg,opts.sorg, sflat, qdups, qlocaldups)

    sout = op.join(out_dir, opts.sorg +
            ".genelist-" + tdate + ".csv")
    """
    link = "http://toxic.berkeley.edu/CoGe/GEvo.pl?prog=blastn&dsid1=" + \
          opts.sdsid + "&dsid2=" + opts.qdsid + \
          "&x1=%(x1)s&x2=%(x2)s&chr1=%(chr1)s&chr2=%(chr2)s&num_seqs=2&autogo=1" 
    """
    if opts.qflat_all != opts.sflat_all:
        write_genelist('s', sout, sflat, pairs, orthos, mcns, link, opts.sorg, opts.qorg, qflat, sdups, slocaldups)