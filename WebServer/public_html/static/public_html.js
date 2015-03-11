var Playback = Object();

$(document).ready(function() {
	Playback.Comet();
});

Playback.Comet = function() {
	if(window.EventSource) {
		var status = new EventSource('status');
		status.addEventListener('status', function(event) {
			Playback.StatusUpdate($.parseJSON(event.data));
		}, false);
		status.addEventListener('open', function(event) {
			$('nav #status-comet:visible').fadeOut(100);
		}, false);
		status.addEventListener('error', function(event) {
			// Closed connection - close the Comet and open another
			if (event.eventPhase == EventSource.CLOSED) {
				$('nav #status-comet:hidden').fadeIn(100);
				status.close();
				setTimeout(function(){ Playback.Comet(); },5000);
				return;
			}
		}, false);
	}
}

Playback.StatusUpdate = function(status) {
	$nav = $('nav');
	$footer = $('footer');
	
	// Playing
	if('Playing' in status) {
		if(status.Playing) {
			$footer.find('#button-toggle').removeClass('glyphicon-play').addClass('glyphicon-pause');
		} else {
			$footer.find('#button-toggle').removeClass('glyphicon-pause').addClass('glyphicon-play');
		}
	}
	
	// Internet
	if('Internet' in status) {
		if(status.Internet) {
			$nav.find('#status-internet:visible').fadeOut(100);
		} else {
			$nav.find('#status-internet:hidden').fadeIn(100);
		}
	}
	
	// TrackInfo
	if('TrackInfo' in status) {
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