var Playback = Object();

$(document).ready(function() {
	if(window.EventSource) {
		var status = new EventSource('playback/comet');
		status.addEventListener('status', function(event) {
			Playback.StatusUpdate($.parseJSON(event.data));
		}, false);
	}
});

Playback.StatusUpdate = function(data) {
	$footer = $('footer');
	if(data.__PLAYING__) {
		$footer.find('.button-toggle').removeClass('glyphicon-play').addClass('glyphicon-pause');
	} else {
		$footer.find('.button-toggle').removeClass('glyphicon-pause').addClass('glyphicon-play');
	}
}

Playback.Toggle = function(reference) {
	var $ref = $(reference);
	if($ref.hasClass('glyphicon-play')) {
		$.post('playback/play', function(data) {});
	} else if($ref.hasClass('glyphicon-pause')) {
		$.post('playback/pause', function(data) {});
	}
}

Playback.Prev = function(reference) {
	var $ref = $(reference);
	if($ref.hasClass('glyphicon-fast-backward')) {
		$.post('playback/prev', function(data) {});
	}
}

Playback.Next = function(reference) {
	var $ref = $(reference);
	if($ref.hasClass('glyphicon-fast-forward')) {
		$.post('playback/next', function(data) {});
	}
}