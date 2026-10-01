document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const formMethod = document.getElementById('method');

    // Tab Controller
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                tabButtons.forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');

                const targetTabId = this.getAttribute('data-target');
                const targetElement = document.getElementById(targetTabId);
                if (targetElement) {
                    targetElement.classList.add('active');
                }

                if (formMethod) {
                    formMethod.value = targetTabId;
                }

                if (targetTabId === 'map') {
                    window.dispatchEvent(new Event('resize'));
                }
            });
        });
    }

    // Search Function
    const searchInput = document.getElementById('enzymeSearch');
    const tableRows = document.querySelectorAll('.enzyme-table tbody tr');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();

            tableRows.forEach(row => {
                const enzymeNameCell = row.cells[1];
                const sequenceCell = row.cells[2];
                const cutsCell = row.cells[3];

                if (enzymeNameCell) {
                    const enzymeName = enzymeNameCell.textContent.toLowerCase();
                    const sequenceName = sequenceCell ? sequenceCell.textContent.toLowerCase() : "";
                    const cutsTotal = cutsCell ? cutsCell.textContent.toLowerCase() : "";

                    if (enzymeName.includes(searchTerm) || sequenceName.includes(searchTerm) || cutsTotal.includes(searchTerm)) {
                        row.style.display = "";
                    } else {
                        row.style.display = "none";
                    }
                }
            });
        });
    }
});

// Downloads
function downloadMap() {
    const plotDiv = document.querySelector('.plotly-graph-div');

    if (plotDiv) {
        Plotly.downloadImage(plotDiv, {
            format: 'png',
            filename: 'restriction_map'
        });
    }
}

function downloadCSV() {
    const table = document.querySelector("#fragments .enzyme-table");

    if (table) {
        let csvContent = "";
        const rows = table.querySelectorAll("tr");

        rows.forEach(row => {
            let rowData = [];
            const cols = row.querySelectorAll("td, th");

            cols.forEach(col => {
                let data = col.innerText.trim();
                data = data.replace(/"/g, '""');
                rowData.push('"' + data + '"');
            });

            csvContent += rowData.join(",") + "\n";
        });

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);

        link.setAttribute("href", url);
        link.setAttribute("download", "restriction_fragments.csv");
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}