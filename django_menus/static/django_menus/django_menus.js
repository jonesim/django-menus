dropdown_menu_function = function (reference, placement = 'bottom-start') {
    var menu = $('#' + reference.attr('id') + '-menu');
    var pop;

    menu.click(function () {
        menu.removeClass('show clicked')
    })

    reference.hover(function (e) {
        var reference = $(this);
        var menu = $('#' + reference.attr('id') + '-menu')
        if (pop == undefined) {
            pop = new Popper(reference, menu, {placement: placement})
        } else {
            pop.update()
        }
        if (reference.is(':hover')) {
            $('.menu-system.show').removeClass('show')
            menu.addClass('show menu-system')
        }
        setTimeout(function () {
            if ((!reference.is(':hover') && !menu.is(':hover')) && !menu.hasClass('clicked')) {
                menu.removeClass('show')
            }
        }, e.type === 'mouseleave' ? 300 : 0);
    })

    menu.hover(function (e) {
        setTimeout(function () {
            if ((!reference.is(':hover') && !menu.is(':hover')) && !menu.hasClass('clicked')) {
                menu.removeClass('show')
            }
        }, e.type === 'mouseleave' ? 300 : 0);
    })

    reference.click(function () {
        if (menu.hasClass('clicked')) {
            menu.removeClass('show clicked')
        } else {
            menu.addClass('show clicked')
        }
    })

    reference.focusout(function () {
        if (menu.hasClass('clicked') &&  !menu.is(':hover')) {
            menu.removeClass('show clicked')
        }
    })
}

dropdown_menu_click = function (reference, placement = 'bottom-start') {
    var menu = $('#' + reference.attr('id') + '-menu');
    var pop;

    menu.click(function () {
        if (menu.hasClass('clicked')) {
            menu.removeClass('show clicked')
        }
    })

    reference.click(function () {
        if (pop == undefined) {
            pop = new Popper(reference, menu, {placement: placement})
        }
        if (menu.hasClass('clicked')) {
            menu.removeClass('show clicked')
        } else {
            menu.addClass('show clicked')
        }
    })

    reference.focusout(function () {
        if (menu.hasClass('clicked') &&  !menu.is(':hover')) {
                menu.removeClass('show clicked')
            }
    })
}