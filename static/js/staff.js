document.addEventListener("DOMContentLoaded", function () {

    const normalCount = Number(document.getElementById("normalData").value);
    const lowCount = Number(document.getElementById("lowData").value);
    const criticalCount = Number(document.getElementById("criticalData").value);

    // BAR CHART
    new Chart(document.getElementById("barChart"), {
        type: "bar",
        data: {
            labels: ["Normal", "Low", "Critical"],
            datasets: [{
                label: "Stock Status",
                data: [normalCount, lowCount, criticalCount],
                backgroundColor: ["#22c55e", "#facc15", "#ef4444"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // PIE CHART
    new Chart(document.getElementById("pieChart"), {
        type: "doughnut",
        data: {
            labels: ["Normal", "Low", "Critical"],
            datasets: [{
                data: [normalCount, lowCount, criticalCount],
                backgroundColor: ["#22c55e", "#facc15", "#ef4444"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

});