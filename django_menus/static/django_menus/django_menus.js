    dropdown_menu_function = function (reference, placement='bottom-start') {
        var menu = $('#' + reference.attr('id') +'-menu');
        var pop;

        reference.hover(function (e) {
            var reference = $(this);
            var menu = $('#' + reference.attr('id') +'-menu')
            if (pop == undefined) {
                pop = new Popper(reference, menu, {placement: placement})
            }
            if (reference.is(':hover')) {
                menu.addClass('show')
            }
            setTimeout(function () {
                if ((!reference.is(':hover') && !menu.is(':hover')) && !menu.hasClass('clicked')) {
                    menu.removeClass('show')
                }
            }, e.type === 'mouseleave' ? 300 : 0);
        })

        menu.hover(function (e) {
            if (menu.is(':hover')) {
                menu.addClass('show')
            }
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
            if (menu.hasClass('clicked')) {
                menu.removeClass('show clicked')
            }
        })
    }