function navigatePageWithUrlParameters(page) {
    'use strict';
    var query = $('#search_query').val();
    var depot_code = $('#depot_code').val();
    var from_date = $('#from_date').val();
    var to_date = $('#to_date').val();
    var retailer_notes_dsr = $('#retailerNotesDSR').val();
    var location = window.location.pathname + '?page=' + page;
    if (!(query === '') && !(query === undefined)) {
        location += '&q=' + query;
    }
    if (!(depot_code === '') && !(depot_code === undefined)) {
        location += '&depot_code=' + depot_code;
    }
    if (!(from_date === '') && !(from_date === undefined)) {
        location += '&from_date=' + from_date;
    }
    if (!(to_date === '') && !(to_date === undefined)) {
        location += '&to_date=' + to_date;
    }
    if (!(retailer_notes_dsr === '') && !(retailer_notes_dsr === undefined)) {
        location += '&dsr=' + retailer_notes_dsr;
    }
    window.location.href = location;
}