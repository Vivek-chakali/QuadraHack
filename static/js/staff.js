const normal = document.getElementById("normalData").value;
const low = document.getElementById("lowData").value;
const critical = document.getElementById("criticalData").value;

const barCtx = document.getElementById("barChart");

new Chart(barCtx, {
type: "bar",

data: {
labels: ["Normal","Low","Critical"],

datasets: [{
label: "Inventory Status",

data: [normal,low,critical],

backgroundColor:[
"#22c55e",
"#facc15",
"#ef4444"
]
}]
},

options:{
responsive:true
}

});

const pieCtx = document.getElementById("pieChart");

new Chart(pieCtx, {
type: "pie",

data:{
labels:["Normal","Low","Critical"],

datasets:[{
data:[normal,low,critical],

backgroundColor:[
"#22c55e",
"#facc15",
"#ef4444"
]
}]
}
});