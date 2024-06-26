hqDefine("hqwebapp/spec/bootstrap3/main", [
    "mocha/js/main",
], function (
    hqMocha
) {
    hqRequire([
        "hqwebapp/spec/assert_properties_spec",
        "hqwebapp/spec/bootstrap3/inactivity_spec",
        "hqwebapp/spec/urllib_spec",
        "hqwebapp/spec/bootstrap3/widgets_spec",
    ], function () {
        hqMocha.run();
    });

    return 1;
});
