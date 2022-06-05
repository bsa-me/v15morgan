odoo.define('education.fullscreen', function(require) {
    "use strict";

console.log('running');


var publicWidget = require('web.public.widget');
var Fullscreen = require('website_slides.fullscreen');
var core = require('web.core');
var QWeb = core.qweb;
var websiteSlidesFullscreenPlayer = publicWidget.registry.websiteSlidesFullscreenPlayer;

Fullscreen.include({

        _renderSlide: function () {
            var slide = this.get('slide');
            var $content = this.$('.o_wslides_fs_content');
            $content.empty();

            if(slide.type == 'iframe'){
                $content.html(QWeb.render('website.slides.fullscreen.iframe', {widget: this}));
            }
            else{
                this._super.apply(this, arguments);
            }
        },

        _preprocessSlideData: function (slidesDataList) {
            slidesDataList.forEach(function (slideData, index) {
                // compute hasNext slide
                slideData.hasNext = index < slidesDataList.length-1;
                // compute embed url
                if (slideData.type === 'video') {
                    slideData.embedCode = $(slideData.embedCode).attr('src');  // embedCode containts an iframe tag, where src attribute is the url (youtube or embed document from odoo)
                    slideData.embedUrl =  "https://" + slideData.embedCode + "&rel=0&autoplay=1&enablejsapi=1&origin=" + window.location.origin;
                } else if (slideData.type === 'infographic') {
                    slideData.embedUrl = _.str.sprintf('/web/image/slide.slide/%s/image_1024', slideData.id);
                } else if (_.contains(['document', 'presentation'], slideData.type)) {
                    slideData.embedUrl = $(slideData.embedCode).attr('src');
                }

                else if(slideData.type === 'iframe'){
                    console.log('iframe');
                    slideData.embedUrl = $(slideData.embedCode).attr('src');
                }

                // fill empty property to allow searching on it with _.filter(list, matcher)
                slideData.isQuiz = !!slideData.isQuiz;
                slideData.hasQuestion = !!slideData.hasQuestion;
                // technical settings for the Fullscreen to work
                slideData._autoSetDone = _.contains(['infographic', 'presentation', 'document', 'webpage'], slideData.type) && !slideData.hasQuestion;
            });
            return slidesDataList;
        },

});


websiteSlidesFullscreenPlayer.include({

    xmlDependencies: (websiteSlidesFullscreenPlayer.prototype.xmlDependencies || []).concat(
        ["/education/static/src/xml/website_slides_fullscreen.xml"]
    )

});

});