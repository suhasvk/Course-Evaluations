// Site.js
$(function(){
	// $('.modal').modal();
	$('#navbar').find('li').each(function(){
		$(this).click(function(evt){
			if (!$(this).hasClass('active')){
				$('.panel').hide();
				var panelIdSelector = $(this).children('a').attr('href') + '-panel';
				$(panelIdSelector).show();
				$('.collapse').collapse('hide');
				if (panelIdSelector === '#results-panel'){
					$('#search-modal').modal('show');
				}
			}
		});
	});
});