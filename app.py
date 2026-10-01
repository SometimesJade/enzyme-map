"""
Flask routes for EnzymeMap.

Collect a DNA sequence, list the enzymes that cut it, and render the
linear or circular restriction map with its fragment table.
"""


from flask import Flask, render_template, request

from process_sequence import (
    get_sequence_input,
    clean_sequence,
    validate_sequence,
    apply_region,
    find_all_enzymes,
)
from map_sequence import (
    map_restriction,
    calculate_fragments,
    plot_circular_map,
    plot_restriction_map,
)

app = Flask(__name__)
app.config['MAX_FORM_MEMORY_SIZE'] = None
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024


@app.route('/', methods=['GET', 'POST'])
def sequence_input():
    """
    Render the sequence-input landing page.

    :returns: The rendered ``sequence_input.html`` template.
    """
    return render_template("sequence_input.html")


@app.route('/analyse_sequence', methods=['GET', 'POST'])
def analyse_sequence():
    """
     Resolve and validate the submitted sequence, then list cutting enzymes.

     Obtains the raw sequence (text, file, or GenBank), cleans and validates
     it, optionally trims it to a sub-region, and finds every commercial
     enzyme that cuts it. Any error re-renders the input page with a message.

     :returns: ``analyse_sequence.html`` with the sequence, circular flag,
               max-cuts limit and matching enzymes on success; otherwise
               ``sequence_input.html`` re-rendered with an ``error``.
     """
    input_data = request.form.to_dict()
    input_file = request.files.get('file')
    sequence, error = get_sequence_input(input_data, input_file)
    if error:
        return render_template("sequence_input.html",
                               error=error)
    elif sequence:
        sequence = clean_sequence(str(sequence))
        invalid = validate_sequence(sequence)
        if invalid:
            return render_template("sequence_input.html",
                                   error=invalid)
        else:
            cut_sequence, error = apply_region(sequence, input_data)
            if error:
                return render_template("sequence_input.html",
                                       error=error)
            circular = request.form.get("circular") == "on"
            max_cuts = input_data.get('max_cuts')
            enzymes, error = find_all_enzymes(cut_sequence, circular, max_cuts)
            if error:
                return render_template("sequence_input.html",
                                       error=error)
            return render_template("analyse_sequence.html",
                                   sequence=cut_sequence,
                                   circular=circular,
                                   max_cuts=max_cuts,
                                   enzymes=enzymes)
    else:
        error = "No sequence provided."
        return render_template("sequence_input.html",
                               error=error)


@app.route('/map_sequence', methods=['POST'])
def map_sequence():
    """
    Map the selected enzymes onto the sequence and render the result.

    Reads the enzymes, sequence and circular flag from the form, calculates
    the cut sites and fragments, and builds a linear or circular Plotly map.

    :returns: ``map_sequence.html`` with the selected enzymes, the embedded
              Plotly map and the fragment list.
    """
    selected_enzymes = request.form.getlist("selected_enzymes")
    sequence = request.form.get("seq", "")
    is_circular = request.form.get("circular") == "True"

    results = map_restriction(sequence, selected_enzymes, is_circular)
    fragments_list = calculate_fragments(results, len(sequence), is_circular)

    if is_circular:
        fig = plot_circular_map(results, len(sequence))
    else:
        fig = plot_restriction_map(results, len(sequence))
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    return render_template("map_sequence.html",
                           selected_enzymes=selected_enzymes,
                           plot_html=plot_html,
                           fragments=fragments_list)


if __name__ == '__main__':
    app.run()
