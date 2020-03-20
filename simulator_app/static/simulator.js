var screen_width=screen.width;
var screen_height=screen.height;
var ww;
var hh;
const INFECTED_COLOR = '#ff4d4d';
const HEALTHY_COLOR = '#4aa175';
const INACTIVE_COLOR = '#BEBEBE';
var orig_nodes_data =[];
var orig_links_data =[];
var nodes_data;
var links_data;
var node;
var link;
var simulation;
var svg = d3.select("svg");
var adj_matrix = [];
var node_to_idx_map = {};
var svg_content;
var infection_count = 0;
var bbb = $("body");

var infection_prob = $('#infection-prob-slider').val();
$('#infection-prob-readout').text(infection_prob);

$('#infection-prob-slider').on('input change', function(e){
    infection_prob = $('#infection-prob-slider').val();
    $('#infection-prob-readout').text(infection_prob);
});

// for adding the modal when the simulation starts
$(document).on({
    ajaxStart: function() { bbb.addClass("loading");    },
     ajaxStop: function() { bbb.removeClass("loading"); }    
});

// initiate in removal mode
var click_mode = "remove";
$('#rm-mode-toggle').prop('checked', true);

$('#rm-mode-toggle').change(
    function(){
        click_mode = "remove";
    }
);

$('#infect-mode-toggle').change(
    function(){
        click_mode = "infect";
    }
);

array_sum = function(v){
    // returns the sum of the array v
    return v.reduce(function(a,b){
        return a + b
    }, 0);
}

function node_color(node_item){
    if(node_item["infected"]){
        return INFECTED_COLOR;
    } else if (!node_item["active"]){
        return INACTIVE_COLOR
    }
    else {
        return HEALTHY_COLOR;
    }
}

function line_maker(link_item){
    if(link_item['visible']){
        return 2;
    } else {
        return 0;
    }
}

function node_alpha(node_item){
    return 0.3+0.7*node_item['infect_pct'];
}

function node_sizer(n){
    // returns a radius based on the number of connections (degree)
    var degree = n["degree"];
    if(degree > 0){
        r = 5 + 5*Math.log(n["degree"]);
    } else {
        r = 5;
    }
    return r;
}

function get_degrees(){

    // calculates the connectivity degree of each node
    // modifies global vars

    node_to_idx_map = {};
    adj_matrix = []

    for (var i=0; i < nodes_data.length; i++){
        adj_matrix[i] = [];
        node_to_idx_map[nodes_data[i]["name"]] = i;
        for(var j=0; j < nodes_data.length; j++){
            adj_matrix[i][j] = 0;
        }
    }

    var i = 0;
    while(i < links_data.length){
        var l = links_data[i];
        var src = l["source"];
        var target = l["target"];
        var src_idx = node_to_idx_map[src["name"]];
        var target_idx = node_to_idx_map[target["name"]];
        adj_matrix[src_idx][target_idx] = 1;
        adj_matrix[target_idx][src_idx] = 1;
        i += 1;
    }

    for(var i=0; i < nodes_data.length; i++){
        nodes_data[i]["degree"] = array_sum(adj_matrix[i]);
    }
}

function node_action(d,i){
    // this function defines the action that happens when a node is clicked

    if(click_mode === 'remove'){

        // set the 'removed' node to inactive so it loses its links and 
        // changes color
        var idx = nodes_data.findIndex( function(x){
            return x["name"] === d["name"];
        });
        nodes_data[idx]["active"] = !nodes_data[idx]["active"];

        // if the node happened to be infected already, we need to decrement the counter
        if (nodes_data[idx]["infected"]){
            infection_count -= 1;
            nodes_data[idx]["infected"] = false;
        }

        var activating_click = nodes_data[idx]["active"];
        // hide or unhide connections involving the node that was removed
        for(var j=0; j<links_data.length; j++){
            var l = links_data[j];
            if ((l.source === d) || (l.target === d)){
                if (activating_click){
                    if ((l.source['active']) & (l.target['active'])){
                        l['visible'] = true;
                    } else {
                        l['visible'] = false;
                    }
                } else {
                    l['visible'] = false;
                }
            }
        }

        redraw();

    } else if(click_mode === 'infect'){

        // toggle the infection status
        d["infected"] = !d["infected"];
        if (d["infected"]){
            infection_count += 1;
        } else {
            infection_count -= 1;
        }
        d3.select(this).attr("fill", node_color);
    }
}

function tickActions() {
    //update circle positions to reflect node updates on each tick of the simulation 
    node.attr(
        "cx", function(d) { return d.x; }
    ).attr(
        "cy", function(d) { return d.y; }
    );

    link
        .attr("x1", function(d) { return d.source.x; })
        .attr("y1", function(d) { return d.source.y; })
        .attr("x2", function(d) { return d.target.x; })
        .attr("y2", function(d) { return d.target.y; });
        
}

function redraw(){
    // This functions is called when there is a change made to the graph through
    // user interaction.

    get_degrees();

    svg.select(".links").selectAll('line')
        .data(links_data, function(d,i){return d.index})
        .join(
            function(enter){
                console.log('enter line');
                return enter.append("line")
                    .attr("stroke-width", line_maker);
            },
            function(update){
                console.log('update line');
                return update
                    .attr("stroke-width", line_maker);
            },
            function(exit){

                return exit           
                    .transition()
                    .duration(500)
                    .attr('stroke-width', 0)
                    .style('opacity', 0);
            }
        );

    svg.selectAll("circle")
        .data(nodes_data, function(d,i) {return d["name"]})
        .join(
            function(enter){
                return enter            
                    .append("circle")
                    .attr("r", node_sizer)
                    .attr("fill", node_color)
                    .on('click', node_action);
            },
            function(update){
                return update.attr("fill", node_color)
                    .attr("fill-opacity", node_alpha);
            },
            function(exit){

                return exit           
                    .transition()
                    .duration(500)
                    .attr('r', 0)
                    .style('opacity', 0)
                    .on('end', function() {
                        d3.select(this).remove();
                    });
            }
        );
}

function zoomed() {
    svg_content.attr("transform", d3.event.transform);
}

function init_setup(){
    // Now that the functions are setup, can setup the graph:

    svg.attr("width", 0.6*screen_width);
    svg.attr("height", 0.5*screen_height);

    // draw a box around the canvas:
    svg.append("rect")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("stroke", "black")
        .attr("stroke-width",2);


    // gets the width/height of the SVG and extracts out its size
    // This is used to position the force-directed graph at the
    // center of the viewing frame
    ww = svg.style("width");
    hh = svg.style("height");
    N = ww.length;
    ww = ww.substring(0,N-2);
    N = hh.length;
    hh = hh.substring(0,N-2);

    // add the 'visible' property so we can control whether the links are visible or not
    for(var j=0; j<links_data.length; j++){
        var l = links_data[j];
        l['visible'] = true;
    }

    // group the links as an element in the SVG
    // put the link group first so they end up behind the nodes
    var link_select = svg.append("g")
        .attr("class", "links")
        .selectAll("line");

    // group the nodes
    var node_select = svg.append("g")
        .attr("class", "nodes")
        .selectAll("circle");

    svg_content = svg.selectAll("g");

    for(var i =0; i<nodes_data.length; i++){
        var n = nodes_data[i];
        n['active'] = true;
    }

    // Now setup the actual force-directed graph:
    simulation = d3.forceSimulation().nodes(nodes_data)
        .force('charge', d3.forceManyBody().strength(-550))
        .force('center', d3.forceCenter(ww/2, hh/2))
        .force('link', d3.forceLink(links_data)
        .id(function(d) { return d.name; }))
        .on('tick', tickActions);

    // need to run this so we fill the adjacency matrix and determine the node sizes based on their connectivity.
    get_degrees();

    link = link_select
        .data(links_data)
        .enter().append("line")
        .attr("stroke-width", line_maker);

    node = node_select
        .data(nodes_data, function(d,i) {return d["name"]})
        .enter()
        .append("circle")
        .attr("r", node_sizer)
        .attr("fill", node_color)
        .on('click', node_action);

}

function on_complete(){

    // zoom functionality
    svg.call(d3.zoom()
        .extent([[0, 0], [ww, hh]])
        .scaleExtent([-8, 8])
        .on("zoom", zoomed));

    // Show the pointer when the user mouses over a node
    d3.selectAll("circle").on(
        "mouseover", 
        function(d,i){
            d3.select(this).style("cursor", "pointer");
        }
    );
}

$("#start-sim").on('click', function(){
    if (infection_count > 0){
        simulate();
    } else {

        alert('You need to infect at least one person first.');
    }
});

$("#reset-sim").on('click', function(){
    console.log('reset');
    for(var j=0; j<nodes_data.length; j++){
        nodes_data[j]["active"] = true;
        nodes_data[j]["infected"] = false;
        nodes_data[j]['infect_pct'] = 1.0;
    }

    for(var j=0; j<links_data.length; j++){
        var l = links_data[j];
        l['visible'] = true;
    }
    infection_count = 0;
    redraw();
});

function display_final_nodes(infected_nodes_pct) {
    for(var i =0; i < nodes_data.length; i++){
        var pct = infected_nodes_pct[i];
        if(pct > 0){
            nodes_data[i]['infected'] = true;
            nodes_data[i]["infect_pct"] = pct;
        } else {
            nodes_data[i]['infected'] = false;
            nodes_data[i]["infect_pct"] = 0;
        }
    }
    redraw();
}

function inject_svg(svg_text){
    
    var _width = 0.4*screen_width;
    var _height = 0.5*_width;
    
    var _svg = d3.select('#history-plot-area').append('svg')
        .attr('width', _width)
        .attr('height', _height);
    _svg.html(svg_text);
}


function plot_results(vpt, hp){
    d3.select('#history-plot-area').selectAll("*").remove();
    inject_svg(vpt);
    inject_svg(hp);
}