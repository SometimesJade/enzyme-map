"""
Restriction-site mapping, fragment calculation and plotting.

Calculates enzyme cut sites for a sequence, derives the resulting
fragments, and builds linear or circular Plotly restriction maps.
"""


import math

import plotly.graph_objects as go
from Bio.Restriction import RestrictionBatch
from Bio.Seq import Seq


def map_restriction(sequence, enzymes, circular):
    """
    Calculate the cut sites of the selected enzymes on the sequence.

    :param sequence: The DNA sequence to digest, as a string.
    :param enzymes: Names of the enzymes to apply.
    :param circular: ``True`` to treat the sequence as circular.
    :returns: A Biopython search result mapping each enzyme to its cut
              positions.
    """
    sequence = Seq(sequence)
    batch = RestrictionBatch(enzymes)
    cut_results = batch.search(sequence, linear=not circular)

    return cut_results


def plot_restriction_map(cut_results, sequence_length):
    """
     Build a linear Plotly map of enzyme cut sites along a sequence.

     Draws a horizontal backbone with labeled end markers and evenly spaced
     ticks. Each enzyme's cuts are plotted as staggered downward triangles
     joined to the backbone by drop lines, with hover text giving the
     position, recognition site and overhang type.

     :param cut_results: Mapping of enzyme objects to cut positions, as
         returned by ``map_restriction``.
     :param sequence_length: Length of the sequence in base pairs.
     :returns: A ``plotly.graph_objects.Figure`` holding the linear map.
     """
    fig = go.Figure()
    fig.add_shape(
        type="line",
        x0=0, y0=0, x1=sequence_length, y1=0,
        line=dict(color="lightgray", width=6)
    )

    fig.add_shape(
        type="line",
        x0=0, y0=0.20, x1=0, y1=-0.20,
        line=dict(color="gray", width=4),
    )

    fig.add_annotation(
        x=0,
        y=0.4,
        text="0bp",
        textangle=0,
        showarrow=False,
    )

    fig.add_shape(
        type="line",
        x0=sequence_length, y0=0.20, x1=sequence_length, y1=-0.20,
        line=dict(color="gray", width=4),
    )

    fig.add_annotation(
        x=sequence_length,
        y=0.4,
        text=f"{sequence_length}bp",
        textangle=0,
        showarrow=False,
    )

    step = max(1, round(sequence_length / 10))
    for dash in range(0, sequence_length, step):
        fig.add_shape(
            type="line",
            x0=dash, y0=0.20, x1=dash, y1=0,
            line=dict(color="gray", width=2),
        )

    y_position = 1
    for enzyme, cuts in cut_results.items():
        enzyme_name = str(enzyme)
        if enzyme.is_blunt():
            end_type = "End Type: Blunt"
        elif enzyme.is_5overhang():
            end_type = "End Type: Sticky (5' Overhang)"
        elif enzyme.is_3overhang():
            end_type = "End Type: Sticky (3' Overhang)"
        else:
            end_type = None

        if cuts:
            staggered_y = [y_position + (i % 3) * 0.6 for i in
                           range(len(cuts))]
            fig.add_trace(go.Scatter(
                x=cuts,
                y=staggered_y,
                mode='markers+text',
                marker=dict(size=12, symbol="triangle-down", color="#006e8e"),
                name=enzyme_name,
                text=[enzyme_name] * len(cuts),
                textposition="top center",
                hovertemplate=f"{enzyme_name}<br>"
                              f"Cut Position: %{{x}}bp<br>"
                              f"Site: {enzyme.elucidate()}<br>"
                              f"{end_type}<br>"
                              f"<extra></extra>"
            ))

            for cut, y_dot in zip(cuts, staggered_y):
                fig.add_shape(
                    type="line",
                    x0=cut, y0=0, x1=cut, y1=y_dot,
                    line=dict(color="gray", width=1, dash="dot")
                )

            y_position += 0.8

    fig.update_layout(
        xaxis=dict(
            title="Position in bp",
            fixedrange=True,
            nticks=25
        ),
        yaxis=dict(
            visible=False,
            range=[-1, y_position + 1],
            fixedrange=True
        ),

        height=400 + (y_position * 40),
        plot_bgcolor='white',
        hovermode="closest",
        showlegend=False
    )

    return fig


def plot_circular_map(cut_results, sequence_length):
    """
    Build a circular (plasmid-style) Plotly map of enzyme cut sites.

    Draws a circular backbone and places each cut as a marker on an outer
    track at the angle for its position, joined to the backbone by a radial
    drop line; successive enzymes use larger radii to avoid overlap. Hover
    text gives the position, recognition site and cut offsets.

    :param cut_results: Mapping of enzyme objects to cut positions, as
        returned by ``map_restriction``.
    :param sequence_length: Length of the sequence in base pairs.
    :returns: A ``plotly.graph_objects.Figure`` holding the circular map.
    """
    fig = go.Figure()
    r = 15

    fig.add_shape(
        type="circle",
        x0=-r, y0=-r, x1=r, y1=r,
        line=dict(color="black", width=4)
    )
    fig.add_shape(
        type="line",
        x0=0, y0=r-1.5, x1=0, y1=r+1.5,
        line=dict(color="lightgray", width=4)
    )
    track_offset = 5

    for enzyme, cuts in cut_results.items():
        enzyme_name = str(enzyme)

        if cuts:
            x_coords = []
            y_coords = []

            for cut in cuts:
                angle = (math.pi / 2) - (cut / sequence_length) * 2 * math.pi

                x = (r + track_offset) * math.cos(angle)
                y = (r + track_offset) * math.sin(angle)

                x_coords.append(x)
                y_coords.append(y)

                backbone_x = r * math.cos(angle)
                backbone_y = r * math.sin(angle)
                fig.add_shape(
                    type="line",
                    x0=backbone_x, y0=backbone_y, x1=x, y1=y,
                    line=dict(color="gray", width=1, dash="dot")
                )

            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers+text',
                marker=dict(size=10, symbol="circle", color="#006e8e"),
                name=enzyme_name,
                text=[enzyme_name] * len(cuts),
                textposition="top center",
                customdata=cuts,
                hovertemplate=f"{enzyme_name}<br>"
                              f"Cut Position: %{{customdata}}bp<br>"
                              f"Site: {enzyme.elucidate()}<br>"
                              f"Ends: {enzyme.fst5, enzyme.fst3}<br>"
                              f"<extra></extra>"
            ))

            track_offset += 2

    max_range = r + track_offset

    fig.update_layout(
        xaxis=dict(visible=False, range=[-max_range, max_range],
                   fixedrange=True),
        yaxis=dict(visible=False, range=[-max_range, max_range],
                   fixedrange=True, scaleanchor="x", scaleratio=1),
        plot_bgcolor='white',
        showlegend=False,
        height=500,
        hovermode="closest",
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig


def _fragment_helper(all_cuts, fragments):
    """
    Append the fragments lying between consecutive cuts.

    :param all_cuts: Cut sites sorted by position, each a
        ``(position, enzyme)`` tuple.
    :param fragments: List of fragment dicts, mutated in place.
    :returns: The same ``fragments`` list with between-cut fragments added.
    """
    for i in range(len(all_cuts) - 1):
        cut1, enz1 = all_cuts[i]
        cut2, enz2 = all_cuts[i + 1]
        length = cut2 - cut1
        if length > 0:
            fragments.append({"name": f"{enz1} - {enz2}",
                              "location": f"{cut1} - {cut2}",
                              "length": length})
    return fragments


def calculate_fragments(cut_results, sequence_length, circular):
    """
    Calculates the restriction fragments produced by a set of cuts.

    Collects and sorts all cut positions, then derives the fragments between
    consecutive cuts. With no cuts, returns one whole-sequence fragment;
    circular sequences add a wrap-around fragment, linear ones add explicit
    start and end fragments.

    :param cut_results: Mapping of enzyme objects to cut positions, as
        returned by ``map_restriction``.
    :param sequence_length: Length of the sequence in base pairs.
    :param circular: ``True`` for a circular sequence, ``False`` for linear.
    :returns: A list of fragment dicts, each with ``name``, ``location`` and
              ``length`` keys.
    """
    all_cuts = []

    for enzyme, cuts in cut_results.items():
        for cut in cuts:
            all_cuts.append((cut, str(enzyme)))

    all_cuts.sort(key=lambda x: x[0])

    fragments = []

    if not all_cuts:
        return [
            {"name": "Uncut Sequence", "location": f"1 - {sequence_length}",
             "length": sequence_length}]

    if not circular:
        first_cut, first_enz = all_cuts[0]
        if first_cut > 1:
            fragments.append({"name": f"Start - {first_enz}",
                              "location": f"1 - {first_cut}",
                              "length": first_cut})

        _fragment_helper(all_cuts, fragments)

        last_cut, last_enz = all_cuts[-1]
        if last_cut < sequence_length:
            fragments.append({"name": f"{last_enz} - End",
                              "location": f"{last_cut} - {sequence_length}",
                              "length": sequence_length - last_cut})

    else:
        _fragment_helper(all_cuts, fragments)

        last_cut, last_enz = all_cuts[-1]
        first_cut, first_enz = all_cuts[0]
        wrap_length = (sequence_length - last_cut) + first_cut

        if len(all_cuts) == 1:
            fragments.append({"name": f"{first_enz} Linearized",
                              "location": f"{first_cut} (Circular)",
                              "length": sequence_length})
        elif wrap_length > 0:
            fragments.append({"name": f"{last_enz} - {first_enz} (Wrap)",
                              "location": f"{last_cut} - {first_cut}",
                              "length": wrap_length})

    return fragments
