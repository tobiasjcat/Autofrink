function load_query_results () {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
        	var result_area = document.getElementById("results_area");
        	results_area.innerHTML = this.responseText;
       }
    };
    var inquery = document.getElementById("search_bar").value;
    if (inquery.length < 2) {
    	return null;
    } else {
    	xhttp.open("GET", "/api/get_query_results/" + inquery, true);
    	xhttp.send();
	}
}

function gif_this_id (inid) {
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function () {
		if (this.readyState == 4) {
			document.getElementById("gifarea").innerHTML = this.responseText;
		} else {
			document.getElementById("gifarea").innerHTML = "Loading " + inid + "...";
		}
	}
	xhttp.open("GET", "/api/get_gif_url/" + inid, true);
	xhttp.send();
}

function create_clips_from_str () {
  var vocab_results_table = document.getElementById("hidden_json_results");
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function () {
    if (this.readyState == 4 && this.status == 200) {
      var result_area = document.getElementById("results_area");
      results_area.innerHTML = this.responseText;
    }
  };
  var inquery = document.getElementById("search_bar").value;
  if (inquery.length < 2) {
    return null;
  } else {
    xhttp.open("POST", "/api/get_words_results/", true);
    payload = {"query":inquery,"vocab_results_table":null}
    if (vocab_results_table){
      payload["vocab_results_table"] = JSON.parse(vocab_results_table.value);
    }
    xhttp.send(JSON.stringify(payload));
  }
}

function check_clip_vocabularys () {
  var query_string = document.getElementById("search_bar").value;
  if (!query_string) {
    return null;
  }
  var xhttp = new XMLHttpRequest();
  var best_match_area = document.getElementById("best_match_area")
	xhttp.onreadystatechange = function () {
		if (this.readyState == 4) {
			best_match_area.innerHTML = this.responseText;
		} else {
			best_match_area.innerHTML = "Loading...";
		}
	}
  xhttp.open("GET", "/api/get_clip_vocabs/" + query_string, true);//what is data validation?
	xhttp.send();
}
