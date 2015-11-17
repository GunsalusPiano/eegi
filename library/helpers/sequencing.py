from library.models import LibrarySequencingBlatResult

NO_BLAT = 'intended clone, no BLAT results (bad)'
NO_MATCH = 'intended clone, does not match BLAT results (bad)'
L4440_BLAT = 'L4440 with BLAT results (bad)'
L4440_NO_BLAT = 'L4440, no BLAT results (good)'
NO_CLONE_BLAT = 'no intended clone with BLAT results (bad)'
NO_CLONE_NO_BLAT = 'no intended clone, no BLAT results (good)'


def get_organized_blat_results():
    """Fetch all blat results from the database, organized as:

        b[sequencing_result] = blats
    """
    blats = (LibrarySequencingBlatResult.objects.all()
             .select_related('library_sequencing', 'clone_hit'))

    b = {}
    for blat in blats:
        seq = blat.library_sequencing
        if seq not in b:
            b[seq] = []
        b[seq].append(blat)

    return b


def categorize_sequences_by_blat_results(seqs):
    s = {
        L4440_NO_BLAT: [],
        NO_CLONE_NO_BLAT: [],
        NO_BLAT: [],
        NO_MATCH: [],
        L4440_BLAT: [],
        NO_CLONE_BLAT: [],
    }

    b = get_organized_blat_results()

    for seq in seqs:
        if seq.source_stock:
            intended_clone = seq.source_stock.intended_clone
        else:
            intended_clone = None

        # Handle no intended clone case
        if not intended_clone:
            if seq in b:
                s[NO_CLONE_BLAT].append(seq)
            else:
                s[NO_CLONE_NO_BLAT].append(seq)

        # Handle L4440 clone case
        elif intended_clone.is_control():
            if seq in b:
                s[L4440_BLAT].append(seq)
            else:
                s[L4440_NO_BLAT].append(seq)

        # Handle intended clone case
        else:
            if seq not in b:
                s[NO_BLAT].append(seq)
            else:
                match = get_match(b[seq], intended_clone)
                if not match:
                    s[NO_MATCH].append(seq)
                else:
                    rank = match.hit_rank
                    if rank not in s:
                        s[rank] = []
                    s[rank].append(seq)

    return s


def get_match(blat_results, intended_clone):
    for x in blat_results:
        if x.clone_hit == intended_clone:
            return x
    return None


def avg(l):
    if l:
        return sum(l) / len(l)
    else:
        return 0


def get_avg_crl(seqs):
    return avg([x.crl for x in seqs])


def get_avg_qs(seqs):
    return avg([x.quality_score for x in seqs])


def get_number_decent_quality(seqs):
    return sum([x.is_decent_quality() for x in seqs])
