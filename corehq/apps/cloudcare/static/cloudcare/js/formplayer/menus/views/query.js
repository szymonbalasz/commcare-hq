/*global Marionette */

hqDefine("cloudcare/js/formplayer/menus/views/query", function () {
    var FormplayerFrontend = hqImport("cloudcare/js/formplayer/app");

    var QueryView = Marionette.View.extend({
        tagName: "tr",
        className: "formplayer-request",
        template: _.template($("#query-view-item-template").html() || ""),

        templateContext: function () {
            var imageUri = this.options.model.get('imageUri');
            var audioUri = this.options.model.get('audioUri');
            var appId = this.model.collection.appId;
            return {
                imageUrl: imageUri ? FormplayerFrontend.getChannel().request('resourceMap', imageUri, appId) : "",
                audioUrl: audioUri ? FormplayerFrontend.getChannel().request('resourceMap', audioUri, appId) : "",
            };
        },
    });

    var QueryListView = Marionette.CollectionView.extend({
        tagName: "div",
        template: _.template($("#query-view-list-template").html() || ""),
        childView: QueryView,
        childViewContainer: "tbody",

        initialize: function (options) {
            this.parentModel = options.collection.models;
        },

        templateContext: function () {
            return {
                title: this.options.title,
            };
        },

        ui: {
            submitButton: '#query-submit-button',
        },

        events: {
            'click @ui.submitButton': 'submitAction',
        },

        submitAction: function (e) {
            e.preventDefault();
            var payload = {};
            var fields = $(".query-field");
            var model = this.parentModel;
            fields.each(function (index) {
                if (this.value !== '') {
                    payload[model[index].get('id')] = this.value;
                }
            });
            if (hqImport('hqwebapp/js/toggles').toggleEnabled('APP_ANALYTICS')) {
                hqImport('analytix/js/kissmetrix').track.event('Case list', {
                    domain: FormplayerFrontend.getChannel().request('currentUser').domain,
                    name: model[0].collection.title,
                });
            }
            FormplayerFrontend.trigger("menu:query", payload);
        },
    });

    return function (data) {
        return new QueryListView(data);
    };
});
