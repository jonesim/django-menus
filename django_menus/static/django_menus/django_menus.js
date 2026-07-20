var dropdown_menu_function = function dropdown_menu_function(reference) {
  var placement = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'bottom-start';
    var menu = $('#' + reference.attr('id') + '-menu');
    var pop;

    menu.click(function () {
        menu.removeClass('show clicked');
    })

    reference.hover(function (e) {
        var reference = $(this);
        var menu = $('#' + reference.attr('id') + '-menu');
        if (pop == undefined) {
            pop = new Popper(reference, menu, {placement: placement});
        } else {
            pop.update();
        }
        if (reference.is(':hover')) {
            $('.menu-system.show').removeClass('show');
            menu.addClass('show menu-system');
        }
        setTimeout(function () {
            if (!reference.is(':hover') && !menu.is(':hover') && !menu.hasClass('clicked')) {
                menu.removeClass('show')
            }
        }, e.type === 'mouseleave' ? 300 : 0);
    });

    menu.hover(function (e) {
        setTimeout(function () {
            if (!reference.is(':hover') && !menu.is(':hover') && !menu.hasClass('clicked')) {
                menu.removeClass('show')
            }
        }, e.type === 'mouseleave' ? 300 : 0);
    });

    reference.click(function () {
        if (menu.hasClass('clicked')) {
            menu.removeClass('show clicked');
        } else {
            menu.addClass('show clicked');
        }
    });

    reference.focusout(function () {
        if (menu.hasClass('clicked') &&  !menu.is(':hover')) {
            menu.removeClass('show clicked');
        }
    });
};

var dropdown_menu_click = function dropdown_menu_click(reference) {
  var placement = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'bottom-start';
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


function click_href(href) {
    var a = document.createElement('a');
    a.style.display = 'none';
    a.href = href;
    document.body.appendChild(a);
    a.click();
    a.remove();
}


ajax_helpers.command_functions.enable_context_menu = function (command) {
    $(document).on("contextmenu", command.selector, function (evt) {
        evt.preventDefault();

        // Create a dictionary (object) to store data attributes and id
        var elementData = {'ajax': 'context_menu', 'pos': [evt.pageX, evt.pageY]};
        elementData['id'] = $(this).attr('id');

        // Get all data attributes and add them to the dictionary
        $.each(this.dataset, function (key, value) {
            elementData[key] = value;
        });
        ajax_helpers.event = evt
        ajax_helpers.post_json({'data': elementData});
    });
}


ajax_helpers.command_functions.context_menu = function (command) {
    if ($("#context-menu").length) {
        $("#context-menu").replaceWith(command.menu);
    } else {
        $("body").append(command.menu);
    }
    var menu = $('#context-menu');

    // Ensure the menu is valid before proceeding
    if (!menu.length) {
        console.error('Dropdown menu not found');
        return;
    }

    // Get the viewport bounds in document coordinates. Context-menu events already
    // provide page coordinates, and AJAX dropdowns send document coordinates below.
    var windowWidth = $(window).width();
    var windowHeight = $(window).height();
    var viewportLeft = $(window).scrollLeft();
    var viewportTop = $(window).scrollTop();
    var viewportRight = viewportLeft + windowWidth;
    var viewportBottom = viewportTop + windowHeight;

    // Get the menu dimensions
    var menuWidth = menu.outerWidth();
    var menuHeight = menu.outerHeight();

    // Calculate the position
    var positionX = 0;
    var positionY = 0;
    var anchorTop;

    if (command.pos === undefined) {
        positionX = ajax_helpers.event.pageX;
        positionY = ajax_helpers.event.pageY;
    } else {
        positionX = command.pos[0];
        positionY = command.pos[1];
        anchorTop = command.pos[2];
    }

    // Keep oversized menus usable rather than allowing them to extend beyond both
    // edges of the viewport.
    var viewportPadding = 8;
    if (menuHeight > windowHeight - (viewportPadding * 2)) {
        menu.css({
            'max-height': (windowHeight - (viewportPadding * 2)) + 'px',
            'overflow-y': 'auto'
        });
        menuHeight = menu.outerHeight();
    }

    // Adjust position to prevent overflow on the right
    if (positionX + menuWidth + viewportPadding > viewportRight) {
        positionX = viewportRight - menuWidth - viewportPadding;
    }
    positionX = Math.max(viewportLeft + viewportPadding, positionX);

    // AJAX dropdowns include the top of their anchor button. Flip those menus
    // directly above the button when they do not fit below it; pointer context
    // menus retain the existing viewport-edge fallback.
    if (positionY + menuHeight + viewportPadding > viewportBottom) {
        if (anchorTop !== undefined && anchorTop - menuHeight - viewportPadding >= viewportTop) {
            positionY = anchorTop - menuHeight;
        } else {
            positionY = viewportBottom - menuHeight - viewportPadding;
        }
    }
    positionY = Math.max(viewportTop + viewportPadding, positionY);

    // Position the menu at the adjusted coordinates
    menu.css({
        display: 'block',
        top: `${positionY}px`,
        left: `${positionX}px`
    });

    // Hide the menu when clicking outside of it
    $(document).on('click.contextMenu', function (e) {
        if (!$(e.target).closest(menu).length) {
            menu.hide();
            // Remove the click event handler after hiding the menu
            $(document).off('click.contextMenu');
        }
    });

    // Hides the menu as soon as you clicked it
    menu.on('click', function (e) {
        menu.hide();
    });

};

function get_ajax_dropdown_menu(button, dropdownViewName, value) {
    // Get the bounding rectangle of the button
    const rect = button.getBoundingClientRect();

    // Convert the viewport-relative rectangle to document coordinates so it uses
    // the same coordinate system as the absolutely positioned context menu.
    const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollY = window.pageYOffset || document.documentElement.scrollTop;
    const x = rect.left + scrollX;
    const y = rect.bottom + scrollY;
    const top = rect.top + scrollY;

    // Prepare data to send
    const data = {
        ajax: dropdownViewName,
        value: value,
        pos: [x, y, top]
    };

    // Call the post_json function with the new data
    ajax_helpers.post_json({'data': data});
}
