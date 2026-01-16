(function($) {
    $(document).ready(function() {
        $('#id_tenant').change(function() {
            var tenantId = $(this).val();
            $.get('/get_shops/', { tenant_id: tenantId }, function(data) {
                $('#id_shop').empty();
                $('#id_shop').append('<option value="">---------</option>');
                $.each(data, function(index, shop) {
                    $('#id_shop').append('<option value="' + shop.id + '">' + shop.name + '</option>');
                });
            });
        });
    });
})(django.jQuery);