var map = L.map('map',{
    worldCopyJump:true,/*
    maxBounds:[
        [-90,-180],
        [90,180]
    ],*/
    maxBoundsViscosity: 1.0
}).setView([20, 0], 2); //only one map, cant scroll endlessly

var nativeMap=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
})//.addTo(map);

var engMap=L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}.png?key=cb1_3ju9_1_3700d3deb651cf84e9745b9f', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap &copy; CARTO'
})//.addTo(map);

//var polyList=L.geoJSON(data).addTo(map);

engMap.addTo(map);
var usingEngMap=true;

//fetch geoJSON file for polygon coords
fetch("/static/countries.geo.json")
    .then(function(response){
        return response.json();
    })
    .then(function(data){
        var polyList=L.geoJSON(data, {
            interactive:false,
            style:{
                color:"#6495ED",
                opacity:0.4,
                weight:0.7,
                fillOpacity:0.05
            }
        }).addTo(map);
    })

document.getElementById('switchMapButton').addEventListener('click',function(){

    if(usingEngMap){
        map.removeLayer(engMap);
        nativeMap.addTo(map);
        document.getElementById('switchMapButton').textContent = "Switch to Simplified Map";
        usingEngMap=false;
    }
    else{
        map.removeLayer(nativeMap);
        engMap.addTo(map);
        document.getElementById('switchMapButton').textContent = "Switch to Detailed Map";
        usingEngMap=true;
    }

});



Promise.all([
    fetch("/coords").then(function(response){
        return response.json();
    }),
    fetch("/articles").then(function(response){
        return response.json();
    })
]).then(function(results){
    var coords=results[0];
    var articleInfo=results[1];

    drawMapLines(articleInfo,coords);
});


/*var popup = L.popup()
    .setLatLng([51.513, -0.09])
    .setContent("I am a standalone popup.")
    .openOn(map);*/

    /*function onMapClick(e) {
    alert("You clicked the map at " + e.latlng);
}

map.on('click', onMapClick);*/

//only recent articles

function recentArticle(article, daysSince){
    var articleDate=new Date(article.published);

    var today= new Date();
    var cutoffDate=new Date();
    cutoffDate.setDate(today.getDate()-daysSince);

    return articleDate>=cutoffDate;
}

function addToSidebar(relationshipPairs,daysSince){
    var articleList=document.getElementById("articleList");

    var sidebarHTML="";

    for(var key in relationshipPairs){
        var groupedArticles=relationshipPairs[key];
        var firstArticle=groupedArticles[0];

        sidebarHTML+="<div class='articleCard'>";
        sidebarHTML+="<h3>"+firstArticle.country+" - " + firstArticle.relatedCountry+"</h3>";
        sidebarHTML+="<p><b>"+groupedArticles.length+"</b> recent articles</p>";
        sidebarHTML+="<p> From the last "+daysSince+" days</p>";

        groupedArticles.forEach(function(article){
            sidebarHTML+="<p>";
            sidebarHTML+="<b>"+article.title+"</b><br>";
            sidebarHTML+="<i>"+article.published+"</i><br>";
            sidebarHTML+="<a href='"+ article.url + "' target='_blank'>Read article:</a>";
            sidebarHTML+="</p>";
        });
        sidebarHTML+="</div>";
    }
    articleList.innerHTML=sidebarHTML;
}

function drawMapLines(articlesTest,coords){
var relationshipPairs={};
var daysSince=60;


articlesTest.forEach(function(article){
    if(!recentArticle(article,daysSince)){
        return;
    }

    if (!relationshipPairs[article.relationshipKey]){
        relationshipPairs[article.relationshipKey]=[];
    }

    relationshipPairs[article.relationshipKey].push(article);
});

for (var key in relationshipPairs){
    var groupedArticles=relationshipPairs[key];
    var firstArticle=groupedArticles[0];

    var country1=coords[firstArticle.country];
    var country2=coords[firstArticle.relatedCountry];

    if(!country1||!country2){
        console.log("Missing coordinates for: ",firstArticle.country, firstArticle.relatedCountry);
        continue;
    }

    var popupText= `
    <b>${firstArticle.country}-${firstArticle.relatedCountry}</b><br>
    <b>${groupedArticles.length} recent article(s)</b><br>
    <b>Displaying articles from the last ${daysSince} days</b><br><br>

    `;



groupedArticles.forEach(function(article){
    popupText+=`
    <div style="margin-bottom: 10px;">
        <b>${article.title}</b><br>
        <i>${article.summary}</i><br>

        <a href="${article.url}" target="_blank">Read article:</a>
        <hr />
    `;

    /*<i>${article.country}</i><br><br>
         ${article.summary}<br><br>*/

    /*if (article.displayType=='pin'){
        var marker = L.marker([article.lat, article.long]).addTo(map);

        marker.bindPopup(popupText);
    }

    else if (article.displayType=="circle"){
        var circle=L.circle([article.lat,article.long],{
            radius:article.radius,
            color:"#DC143C",
            fillOpacity:0.15

        }).addTo(map);
        circle.bindPopup(popupText);
    }

    else if (article.displayType=="line"){
        var line=L.polyline([
            [article.lat, article.long],
            [article.relLat, article.relLong]

        ],{
            weight:7,
            opacity:0.25,
            color:"red"
        }).addTo(map);
        line.bindPopup(popupText);
        line.bringToFront();
    }*/
});

var line=L.polyline([
            [country1.lat, country1.long],
            [country2.lat, country2.long]

        ],{
            weight:5.75,
            opacity:0.25,
            color:"red"
        }).addTo(map);
        line.bindPopup(popupText);
        line.bringToFront();
}

addToSidebar(relationshipPairs,daysSince);
}