"""
Sequence acquisition, cleaning and validation for EnzymeMap.

Turns user input (typed text, an uploaded file, or a GenBank accession)
into a clean, validated DNA string, and provides the enzyme search that
populates the analysis page.
"""


import urllib.error

from Bio import Entrez, SeqIO
from Bio.Restriction import CommOnly
from Bio.Seq import Seq


Entrez.email = "s1150944@student.hsleiden.nl"


def get_sequence_input(input_type, input_file):
    """
    Obtain a raw sequence from the user's chosen input method.

    Fetches the sequence from a GenBank accession (via NCBI Entrez), an
    uploaded file, or a text field. All inputs are size-limited and
    GenBank lookups are guarded against network and parsing errors.

    :param input_type: The submitted form fields as a dict; must hold a
        ``method`` key (``'genbank'``, ``'file'`` or ``'text'``) plus the
        relevant value (``accession`` or ``sequence``).
    :param input_file: The uploaded file object, or ``None``. Used only when
        the method is ``'file'``.
    :returns: A ``(sequence, error)`` tuple. On success ``sequence`` is the
              raw sequence as a` `str`` and ``error``is ``None``;
              on failure ``sequence`` is ``None`` and ``error``
              is a message.
    """
    if input_type["method"] == "genbank":
        accession = input_type["accession"].strip()
        if not accession:
            return None, "Please provide a valid accession number"
        try:
            with Entrez.esummary(db="nucleotide",
                                 id=accession,
                                 retmode="xml") as handle:
                records = Entrez.read(handle)
                sequence_length = int(records[0]["Length"])
                if sequence_length > 1000000:
                    return None, "Sequence exceeds 1000kb"

            with Entrez.efetch(db="nucleotide",
                               id=accession,
                               rettype="fasta",
                               retmode="text") as handle:
                record = SeqIO.read(handle, "fasta")
                return str(record.seq), None

        except urllib.error.HTTPError as e:
            return None, (f"Could not fetch {accession} from Genbank. "
                          f"HTTP Error: {e.code}")
        except urllib.error.URLError as e:
            return None, (f"Network Error: Could not connect to Genbank. "
                          f"{e.reason}")
        except ValueError:
            return None, f"Could not parse {accession} from Genbank. "
        except RuntimeError as e:
            return None, f"An Error occured: {e}"

    if input_type["method"] == "file":
        if input_file is None:
            return None, "No file was uploaded."
        raw = input_file.read().decode("utf-8", errors="ignore")
        if len(raw) > 1000000:
            return None, "Sequence exceeds 1000kb"
        return raw, None

    if input_type["method"] == "text":
        sequence = input_type["sequence"]
        if len(sequence) > 1000000:
            return None, "Sequence exceeds 1000kb"
        return sequence, None

    return None, "Something went wrong"


def clean_sequence(raw):
    """
    Strip FASTA headers and whitespace from a raw sequence.

    :param raw: The raw sequence text, optionally in FASTA format.
    :returns: The cleaned sequence as a single upper-case string.
    """
    sequence_fragments = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith(">"):
            continue
        sequence_fragments.append(line)

    sequence = "".join(sequence_fragments)

    return sequence.upper()


def validate_sequence(seq):
    """
    Check that a cleaned sequence is usable for analysis.

    Rejects empty or very short sequences and any sequence containing
    characters outside the IUPAC set ``A, C, G, T, N``.

    :param seq: The cleaned, upper-case sequence to validate.
    :returns: ``None`` if the sequence is valid, otherwise an error message
              describing the first problem found.
    """
    if not seq:
        return "Please enter a DNA sequence."
    if len(seq) < 10:
        return "Sequence is too short."
    invalid = sorted(set(seq) - set("ACGTN"))
    if invalid:
        return (f"Sequence contains invalid characters: "
                f"{', '.join(invalid)}. Only A, C, G, T, N are allowed.")
    return None


def apply_region(seq, input_data):
    """
     Optionally restrict the sequence to a user-specified region.

     If valid 1-based ``region_start`` and ``region_end`` values are given,
     returns that slice; if both are absent, returns the sequence unchanged.
     Out-of-range or non-numeric values yield an error message.

     :param seq: The full cleaned sequence.
     :param input_data: The submitted form fields as a dict, optionally
         holding ``region_start`` and ``region_end`` as strings.
     :returns: A ``(sequence, error)`` tuple: the selected (or original)
               sub-sequence with ``error`` ``None``, or ``None`` with an error
               message if the region is invalid.
     """
    start = input_data.get("region_start", "").strip()
    end = input_data.get("region_end", "").strip()
    if start and end:
        try:
            if int(start) >= int(end):
                return None, ("Start of region can not be "
                              "larger than end of region")
            if int(start) >= 1 and int(end) <= len(seq):
                return seq[int(start):int(end)], None
            else:
                return None, ("Region is outisde of sequence "
                              "or cut sequence is too short")
        except ValueError:
            return None, "Only numbers are allowed"
    return seq, None


def find_all_enzymes(sequence, circular, max_cuts):
    """
    Find every commercial enzyme that cuts the sequence.

    Searches the Biopython commercial-enzyme set (``CommOnly``), keeping only
    enzymes that cut and excluding any that cut more than ``max_cuts`` times
    (default 100, to keep the result manageable).

    :param sequence: The cleaned DNA sequence to search.
    :param circular: ``True`` to treat the sequence as circular.
    :param max_cuts: Upper bound on cut sites, as a string or int; falls back
        to 100 when not provided.
    :returns: An ``(enzymes, error)`` tuple: a list of dicts sorted by name
              (each with ``name``, ``site`` and ``cuts``) with ``error``
              ``None``, or ``None`` with ``"No enzymes found."`` if none match.
    """
    search_results = CommOnly.search(Seq(sequence), linear=not circular)
    matched_enzymes = []
    limit = int(max_cuts) if max_cuts else 100

    for enzyme, cut_positions in search_results.items():
        num_cuts = len(cut_positions)
        if num_cuts == 0:
            continue
        if limit and num_cuts > limit:
            continue

        matched_enzymes.append({
            "name": str(enzyme),
            "site": enzyme.elucidate(),
            "cuts": num_cuts
        })
    if matched_enzymes:
        return sorted(matched_enzymes,
                      key=lambda sort: sort["name"]), None
    else:
        return None, "No enzymes found."
