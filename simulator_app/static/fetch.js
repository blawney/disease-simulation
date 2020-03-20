// This assumes jQuery was previously loaded, so we can use its ajax functions

$.ajax({
    type: 'GET',
    url: '/generate-graph',
    success: function(data){
        nodes_data = data["nodes"];
        links_data = data["neighbors"];
        init_setup();
    },
    error: function(){
        console.log('error!');
    },
    complete: function(){
        on_complete();
    }
});

function subset_node(x) {
    return {
        "name": x['name'], 
        "infected": x['infected']
    }
}

// d3 adds a bunch of extra data, which we don't need on the backend
// This functions cleans it to send only that which is necessary
function subset_link(result, x){
    if (x['visible']){
        var item = {
            "source": x["source"]["name"],
            "target": x["target"]["name"],
        }
        return result.concat(item);
    } else {
        return result;
    }
}

function simulate(){
    var data = {
        'nodes': nodes_data.map(subset_node),
        'links': links_data.reduce(subset_link, []),
        'infection_prob' : $('#infection-prob-slider').val()
    }
    console.log(data);
    $.ajax({
        type: 'POST',
        data: JSON.stringify(data),
        contentType: "application/json",
        url: '/simulate-graph',
        success: function(data){
            var infected_nodes_pct = data['infected_nodes_pct'];
            display_final_nodes(infected_nodes_pct);
            plot_results(data['vpt'], data['hp']);
        },
        error: function(){
            console.log('error!');
        }
    });
}