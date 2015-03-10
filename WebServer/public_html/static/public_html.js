var Playback = Object();

$(document).ready(function() {
	if(window.EventSource) {
		var status = new EventSource('status');
		status.addEventListener('status', function(event) {
			Playback.StatusUpdate($.parseJSON(event.data));
		}, false);
	}
});

Playback.StatusUpdate = function(status) {
	$nav = $('nav');
	$footer = $('footer');
	
	// 'Playing'
	if(status.Playing) {
		$footer.find('#button-toggle').removeClass('glyphicon-play').addClass('glyphicon-pause');
	} else {
		$footer.find('#button-toggle').removeClass('glyphicon-pause').addClass('glyphicon-play');
	}
	
	// 'Internet'
	if(status.Internet) {
		$nav.find('#status-internet').fadeOut(100);
	} else {
		$nav.find('#status-internet').fadeIn(100);
	}
	
	// 'TrackInfo'
	if(status.TrackInfo) {
		$footer.find('#info-title').html(status.TrackInfo.title)
		$footer.find('#info-artist').html(status.TrackInfo.artist)
		$footer.find('#info-album').html(status.TrackInfo.album)
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