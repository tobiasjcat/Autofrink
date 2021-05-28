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
    xhttp.open("GET", "/api/get_words_results/" + inquery, true);
    xhttp.send();
  }

}
