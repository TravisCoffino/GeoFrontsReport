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

var engMap=L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=cb1_3ju9_1_3700d3deb651cf84e9745b9f', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap &copy; CARTO'
})//.addTo(map);

//var polyList=L.geoJSON(data).addTo(map);

engMap.addTo(map);
var usingEngMap=true;

//No country at start
var routeMode= "all";
var routeRecords= [];
var countryLayer= null;
var selectedCountry= null;
var countryCenters = {};
var routeAnimationTimers = [];
var currentRelationshipPairs = {};
var currentSidebarDaysSince = 30;

var countryNameAliases = {
    "United States of America": "United States",
    "Democratic Republic of the Congo": "Democratic Republic of Congo",
    "United Republic of Tanzania": "Tanzania",
    "Czech Republic": "Czechia",
    "Ivory Coast": "Côte d'Ivoire",
    "Turkey": "Turkiye"
};

function normalizeCountryName(countryName) {
    return countryNameAliases[countryName] || countryName;
}

function calculateRingCenter(ring) {
    var signedArea = 0;
    var centerX = 0;
    var centerY = 0;

    for (var pointIndex = 0; pointIndex < ring.length - 1; pointIndex++) {
        var currentPoint = ring[pointIndex];
        var nextPoint = ring[pointIndex + 1];
        var crossProduct =
            currentPoint[0] * nextPoint[1] -
            nextPoint[0] * currentPoint[1];

        signedArea += crossProduct;
        centerX += (currentPoint[0] + nextPoint[0]) * crossProduct;
        centerY += (currentPoint[1] + nextPoint[1]) * crossProduct;
    }

    signedArea /= 2;

    if (Math.abs(signedArea) < 0.000001) {
        return null;
    }

    return {
        area: Math.abs(signedArea),
        lat: centerY / (6 * signedArea),
        lng: centerX / (6 * signedArea)
    };
}

function calculateCountryCenter(geometry) {
    var polygons = geometry.type === "Polygon"
        ? [geometry.coordinates]
        : geometry.coordinates;
    var totalArea = 0;
    var weightedLat = 0;
    var weightedLng = 0;

    polygons.forEach(function (polygon) {
        var polygonCenter = calculateRingCenter(polygon[0]);

        if (!polygonCenter) {
            return;
        }

        totalArea += polygonCenter.area;
        weightedLat += polygonCenter.lat * polygonCenter.area;
        weightedLng += polygonCenter.lng * polygonCenter.area;
    });

    if (totalArea === 0) {
        return null;
    }

    return {
        lat: weightedLat / totalArea,
        lng: weightedLng / totalArea
    };
}

function getCountryPoint(countryName, fallbackCoords) {
    var normalizedName = normalizeCountryName(countryName);
    var center = countryCenters[normalizedName];

    if (center) {
        return center;
    }

    var fallback = fallbackCoords[countryName] || fallbackCoords[normalizedName];

    if (!fallback) {
        return null;
    }

    return {
        lat: fallback.lat,
        lng: fallback.long
    };
}

var normalCountryStyle = {
    color: "#6495ED",
    opacity: 0.4,
    weight: 0.7,
    fillOpacity: 0.05
};

var selectedCountryStyle = {
    color: "#244fc7",
    opacity: 1,
    weight: 2,
    fillColor: "#6495ED",
    fillOpacity: 0.25
}


function setupCountryLayer(countryData) {
    countryData.features.forEach(function (feature) {
        var countryName = normalizeCountryName(feature.properties.name);
        var center = calculateCountryCenter(feature.geometry);

        if (center) {
            countryCenters[countryName] = center;
        }
    });

    countryLayer = L.geoJSON(countryData, {
        interactive: true,

        style: function () {
            return normalCountryStyle;
        },

        onEachFeature: function (feature, layer) {
            layer.on("click", function () {
                if (routeMode !== "country") {
                    return;
                }

                showRoutesForCountry(
                    normalizeCountryName(feature.properties.name),
                    layer
                );
            });
        }
    }).addTo(map);
}

document.getElementById('switchMapButton').addEventListener('click',function(){
    var switchButton = document.getElementById('switchMapButton');

    if(usingEngMap){
        map.removeLayer(engMap);
        nativeMap.addTo(map);
        switchButton.classList.remove("showDetailedLabel");
        switchButton.classList.add("showSimplifiedLabel");
        switchButton.setAttribute("aria-label", "Switch to Simplified Map");
        usingEngMap=false;
    }
    else{
        map.removeLayer(nativeMap);
        engMap.addTo(map);
        switchButton.classList.remove("showSimplifiedLabel");
        switchButton.classList.add("showDetailedLabel");
        switchButton.setAttribute("aria-label", "Switch to Detailed Map");
        usingEngMap=true;
    }

});



Promise.all([
    fetch("/static/countries.geo.json").then(function(response){
        return response.json();
    }),
    fetch("/coords").then(function(response){
        return response.json();
    }),
    fetch("/articles").then(function(response){
        return response.json();
    })
]).then(function(results){
    var countryData=results[0];
    var coords=results[1];
    var articleInfo=results[2];

    setupCountryLayer(countryData);
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

function addToSidebar(relationshipPairs,daysSince,searchQuery){
    var articleList=document.getElementById("articleList");
    var normalizedQuery = (searchQuery || "").trim().toLocaleLowerCase();
    var sidebarHTML="";
    var visibleRelationshipCount = 0;

    for(var key in relationshipPairs){
        var groupedArticles=relationshipPairs[key];
        var firstArticle=groupedArticles[0];
        var relationshipSearchText = (
            firstArticle.country + " " + firstArticle.relatedCountry
        ).toLocaleLowerCase();

        if (
            normalizedQuery &&
            !relationshipSearchText.includes(normalizedQuery)
        ) {
            continue;
        }

        visibleRelationshipCount += 1;

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

    if (visibleRelationshipCount === 0) {
        sidebarHTML = "<p class='noRelationshipResults'>" +
            "No country relationships match your search." +
            "</p>";
    }

    articleList.innerHTML=sidebarHTML;
}

function stableRouteDirection(routeKey) {
    var hash = 0;

    for (var characterIndex = 0; characterIndex < routeKey.length; characterIndex++) {
        hash = ((hash << 5) - hash) + routeKey.charCodeAt(characterIndex);
        hash |= 0;
    }

    return Math.abs(hash) % 2 === 0 ? 1 : -1;
}

function createCurvedRoutePoints(startPoint, endPoint, routeKey) {
    var latDifference = endPoint.lat - startPoint.lat;
    var lngDifference = endPoint.lng - startPoint.lng;
    var routeDistance = Math.sqrt(
        latDifference * latDifference + lngDifference * lngDifference
    );
    var curveAmount = Math.min(Math.max(routeDistance * 0.16, 4), 28);
    var direction = stableRouteDirection(routeKey);
    var perpendicularLat = routeDistance === 0
        ? 0
        : (-lngDifference / routeDistance) * curveAmount * direction;
    var perpendicularLng = routeDistance === 0
        ? 0
        : (latDifference / routeDistance) * curveAmount * direction;
    var controlPoint = {
        lat: (startPoint.lat + endPoint.lat) / 2 + perpendicularLat,
        lng: (startPoint.lng + endPoint.lng) / 2 + perpendicularLng
    };
    var curvePoints = [];
    var pointCount = 36;

    for (var pointIndex = 0; pointIndex <= pointCount; pointIndex++) {
        var progress = pointIndex / pointCount;
        var inverseProgress = 1 - progress;
        var latitude =
            inverseProgress * inverseProgress * startPoint.lat +
            2 * inverseProgress * progress * controlPoint.lat +
            progress * progress * endPoint.lat;
        var longitude =
            inverseProgress * inverseProgress * startPoint.lng +
            2 * inverseProgress * progress * controlPoint.lng +
            progress * progress * endPoint.lng;

        curvePoints.push([latitude, longitude]);
    }

    return curvePoints;
}

function clearRouteAnimations() {
    routeAnimationTimers.forEach(function (timer) {
        clearTimeout(timer);
    });
    routeAnimationTimers = [];
}

function animateRouteLine(line, delay) {
    var timer = setTimeout(function () {
        if (!line._path || !map.hasLayer(line)) {
            return;
        }

        var path = line._path;
        var pathLength = path.getTotalLength();

        path.style.transition = "none";
        path.style.strokeDasharray = pathLength + " " + pathLength;
        path.style.strokeDashoffset = pathLength;
        path.getBoundingClientRect();

        requestAnimationFrame(function () {
            path.style.transition = "stroke-dashoffset 850ms ease-out";
            path.style.strokeDashoffset = "0";
        });

        path.addEventListener("transitionend", function finishAnimation() {
            path.style.transition = "";
            path.style.strokeDasharray = "";
            path.style.strokeDashoffset = "";
        }, {once: true});
    }, delay);

    routeAnimationTimers.push(timer);
}

function drawMapLines(articlesTest,coords){
    var relationshipPairs={};
    var daysSince=30;


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

        var country1=getCountryPoint(firstArticle.country, coords);
        var country2=getCountryPoint(firstArticle.relatedCountry, coords);

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
        <div class="popupArticle">
            <b>${article.title}</b><br>
            <i>${article.summary}</i><br>

            <a href="${article.url}" target="_blank">Read article:</a>
            <hr />
        </div>
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

    var routePoints = createCurvedRoutePoints(
        country1,
        country2,
        firstArticle.relationshipKey
    );
    var line=L.polyline(routePoints, {
        weight: 3.5,
        opacity: 0.3,
        color: "red",
        className: "relationship-line"
    });

    routeRecords.push({
        line: line,
        country1: firstArticle.country,
        country2: firstArticle.relatedCountry,
        routePoints: routePoints
    });

    if (
        routeMode === "all" ||
        selectedCountry === normalizeCountryName(firstArticle.country) ||
        selectedCountry === normalizeCountryName(firstArticle.relatedCountry)
    ) {
        line.addTo(map);
    }
        line.bindPopup(popupText, {
            maxWidth: 380,
            maxHeight: 320,
            autoPan: true,
            keepInView: true
        });
        line.bringToFront();
}

currentRelationshipPairs = relationshipPairs;
currentSidebarDaysSince = daysSince;
addToSidebar(
    relationshipPairs,
    daysSince,
    document.getElementById("relationshipSearch").value
);
}

function hideEveryRoute() {
    clearRouteAnimations();

    routeRecords.forEach(function (route) {
        if (map.hasLayer(route.line)){
            map.removeLayer(route.line);
        }
    });
}

function showAllRoutes() {
    routeMode = "all";
    selectedCountry = null;
    routeRecords.forEach(function(route){
        route.line.setLatLngs(route.routePoints);
        route.line.setStyle({
            weight: 3.5,
            opacity: 0.3
        });
        route.line.addTo(map);
    });

    if (countryLayer){
        countryLayer.resetStyle();
    }

    document.getElementById("selectedCountryLabel").textContent="";

    setActiveRouteButton("showAllRoutesButton");
}

function startCountryExploration() {
    routeMode = "country";
    selectedCountry = null;

    hideEveryRoute();

    if (countryLayer){
        countryLayer.resetStyle();
    }

    document.getElementById("selectedCountryLabel").textContent=
    "Click a country to reveal its routes."

    setActiveRouteButton("exploreCountryButton");
}

function showRoutesForCountry(countryName, clickedLayer){
    selectedCountry = normalizeCountryName(countryName);
    hideEveryRoute();

    var visibleRouteIndex = 0;

    routeRecords.forEach(function (route){
        var isConnected=
            normalizeCountryName(route.country1) === selectedCountry ||
            normalizeCountryName(route.country2) === selectedCountry;

        if (isConnected){
            var startsAtFirstCountry =
                normalizeCountryName(route.country1) === selectedCountry;
            var animatedPoints = startsAtFirstCountry
                ? route.routePoints
                : route.routePoints.slice().reverse();

            route.line.setLatLngs(animatedPoints);
            route.line.setStyle({
                weight: 4,
                opacity: 0.65
            });
            route.line.addTo(map);
            route.line.bringToFront();
            animateRouteLine(route.line, visibleRouteIndex * 45);
            visibleRouteIndex += 1;
        }
    });

    if(countryLayer){
        countryLayer.resetStyle();
    }

    clickedLayer.setStyle(selectedCountryStyle);
    clickedLayer.bringToFront();

    document.getElementById("selectedCountryLabel").textContent=
        "Showing routes for " + selectedCountry;
}

function setActiveRouteButton(activeButtonId) {
    document
        .querySelectorAll("#routeControls button")
        .forEach(function (button) {
            button.classList.remove("active");
        });

    document.getElementById(activeButtonId).classList.add("active");
}

document
    .getElementById("showAllRoutesButton")
    .addEventListener("click", showAllRoutes);

document
    .getElementById("exploreCountryButton")
    .addEventListener("click", startCountryExploration);

document
    .getElementById("relationshipSearch")
    .addEventListener("input", function (event) {
        addToSidebar(
            currentRelationshipPairs,
            currentSidebarDaysSince,
            event.target.value
        );
    });
