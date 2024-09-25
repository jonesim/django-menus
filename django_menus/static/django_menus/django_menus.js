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

    // Get the window dimensions
    var windowWidth = $(window).width();
    var windowHeight = $(window).height();

    // Get the menu dimensions
    var menuWidth = menu.outerWidth();
    var menuHeight = menu.outerHeight();

    // Calculate the position
    var positionX = 0;
    var positionY = 0;

    if (command.pos === undefined) {
        positionX = ajax_helpers.event.pageX;
        positionY = ajax_helpers.event.pageY;
    } else {
        positionX = command.pos[0];
        positionY = command.pos[1];
    }
    // Adjust position to prevent overflow on the right
    if (positionX + menuWidth > windowWidth) {
        positionX = windowWidth - menuWidth;
    }

    // Adjust position to prevent overflow on the bottom
    if (positionY + menuHeight > windowHeight) {
        positionY = windowHeight - menuHeight;
    }

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

    // Calculate the x and y coordinates for the bottom-left corner
    const x = rect.left; // X coordinate (horizontal position from the left)
    const y = rect.bottom; // Y coordinate (vertical position from the top of the viewport)

    // Prepare data to send
    const data = {
        ajax: dropdownViewName,
        value: value,
        pos: [x, y] // Send the x and y coordinates
    };

    // Call the post_json function with the new data
    ajax_helpers.post_json({'data': data});
}
