$(document).ready(function () {
$('.oe_website_registration').each(function () {
    var oe_website_registration = this;

    var $shippingDifferent = $("select[name='shipping_id']", oe_website_registration);
    $shippingDifferent.change(function (event) {
        var value = +$shippingDifferent.val();
        var data = $shippingDifferent.find("option:selected").data();
        var $snipping = $(".js_shipping", oe_website_registration);
        var $inputs = $snipping.find("input");
        var $selects = $snipping.find("select");

        $snipping.toggle(!!value);
        $inputs.attr("readonly", value <= 0 ? null : "readonly" ).prop("readonly", value <= 0 ? null : "readonly" );
        $selects.attr("disabled", value <= 0 ? null : "disabled" ).prop("disabled", value <= 0 ? null : "disabled" );

        $inputs.each(function () {
            $(this).val( data[$(this).attr("name")] || "" );
        });
    });

    // change for css
    $(oe_website_registration).on('mouseup touchend', '.js_publish', function (ev) {
        $(ev.currentTarget).parents(".thumbnail").toggleClass("disabled");
    });

    $(oe_website_registration).on("change", ".oe_cart input.js_quantityy", function () {
        var $input = $(this);
        var value = parseInt($input.val(), 10);
        var line_id = parseInt($input.data('line-id'),10);
        var fieldType =$input.attr('id');
        
        if (isNaN(value)) value = 0;
        openerp.jsonRpc("/shop/cart/writeToDB", 'call', {
            'line_id': line_id,
            'value': value,
            'fieldType':fieldType})
    });

});
});
