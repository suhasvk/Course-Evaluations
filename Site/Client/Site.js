// Site.js
$(function(){
	
	//HANDLES NAVBAR INTERACTION
	$('#navbar').find('li').each(function(){

		$(this).click(function(evt){

			if (!$(this).hasClass('active')){

				var panelIdSelector = $(this).children('a').attr('href') + '-panel';
				$('.panel').hide(); //Hides all panels
				$(panelIdSelector).show(); //Shows relevant panel
				$('.collapse').collapse('hide'); //Collapses navbar if necessary
				if (panelIdSelector === '#results-panel'){
					$('#search-modal').modal('show');
				}
			}
		});
	});

});