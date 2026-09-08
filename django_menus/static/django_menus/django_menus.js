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
        if (reference.is(':hover')) {
            $('.menu-system.show').removeClass('show');
            menu.addClass('show menu-system');
            // Positioned only once the menu is shown: a display:none element measures 0x0, so a
            // Popper built before the menu is visible lays it out with no width and cannot see
            // that it overflows the window.
            if (pop == undefined) {
                pop = new Popper(reference, menu, {placement: placement});
            } else {
                pop.update();
            }
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
        if (menu.hasClass('clicked')) {
            menu.removeClass('show clicked')
        } else {
            menu.addClass('show clicked')
            // Positioned only once the menu is shown: a display:none element measures 0x0, so a
            // Popper built before the menu is visible lays it out with no width and cannot see
            // that it overflows the window. Updated on every reopen because the page can have
            // been laid out again since the Popper was built.
            if (pop == undefined) {
                pop = new Popper(reference, menu, {placement: placement})
            } else {
                pop.update()
            }
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


/* Swallow a repeat click on a menu link that is already navigating.
 *
 * Every item this library renders is an <a href>, and a menu item can point at a view that DOES
 * something rather than one that just shows a page. A double-click sends the URL twice, and a
 * view that resolves "what should I act on" from its own current state rather than from the state
 * the link was drawn against acts on both: in JMS Cloud, two clicks on the project timeline's
 * "Go to Next Stage" moved a batch two stages on. Rather than every such view growing its own
 * guard, a project can opt in here.
 *
 * OFF by default: swallowing a click is a behaviour change, and whether a project has menu items
 * pointing at views that mind being called twice is the project's business, not this library's.
 * Opt in with the milliseconds to hold a link for, at whichever level fits - they cascade
 * item -> menu -> page -> off:
 *
 *     MenuItem('next_stage', 'Go to Next Stage', django_menus_repeat_click_ms=2000)
 *     HtmlMenu(request, 'button_group', django_menus_repeat_click_ms=2000)
 *     class MyView(MenuTemplateView):
 *         repeat_click_ms = 2000
 *
 * The first two render data-django-menus-repeat-ms on the anchor; the last sets the window
 * below. An item's own value wins, so one item can be held on a page with the guard off, and
 * 0 on an item opts it out where the page has it on.
 *
 * Read on each click rather than captured at load, so it can be changed at any point in a page's
 * life. An assignment made BEFORE this file loads survives too (see the initialiser below), so
 * a project can set it either side of the include.
 *
 * Around 2000 is a sensible starting point. Note what that window is and is not: it collapses a
 * double-click, which is the reported problem. It does not cover an impatient re-click several
 * seconds into a slow response - holding a link until the page actually goes away would strand
 * anything that deliberately leaves the page in place, like a download or a target="_blank".
 *
 * WHAT IS GUARDED, once on: any marked anchor whose href is not javascript: or a fragment, on an
 * unmodified primary-button click. That is a real browser navigation, so the first click has
 * already started one and a repeat can only duplicate it - which is what keeps this
 * behaviour-neutral for an ordinary page link. A target="_blank" item is included even though
 * the page stays put, because the duplicate REQUEST is the thing being prevented, not the
 * navigation; the effect is one new tab per double-click instead of two.
 *
 * WHAT IS NOT: a javascript: href, because the page stays and clicking again straight away is
 * often exactly what the user means - close a modal, reopen it. That covers AJAX_BUTTON,
 * AJAX_COMMAND, JAVASCRIPT and AJAX_GET_URL_NAME items, a django-modals show_modal link, and
 * anything disabled. Be aware this is a rule about the href, not a guarantee about the effect:
 * a JAVASCRIPT item is free to set window.location itself, an AJAX_BUTTON's view can answer with
 * a redirect command, and AJAX_GET_URL_NAME fetches a view and pushes state. Those reach a view
 * twice on a double-click just the same and are deliberately out of scope here - a view behind
 * one of them needs to be idempotent, or to do its own guarding. Modified clicks (ctrl/cmd/
 * shift/alt, or any button but the primary) are also left alone: they open the link elsewhere
 * and leave this page where it is.
 *
 * Delegated from the document, so it also covers items rendered into the page later - an ajax
 * tooltip's contents, a context menu, a menu replaced by an ajax response. A project that
 * overrides these templates with its own copies needs to carry the marker class across for
 * those menus to be covered.
 *
 * This is defence in depth, NOT a substitute for making such a view idempotent. The back button,
 * a refresh, a second tab, a page left open while someone else moved the record, and a click
 * landing before this script has run all still send the request twice.
 */

// window.* rather than a bare 0, so an assignment made above the include is not clobbered when
// this line runs. A plain `var x = 0` would silently switch the guard back off for a project
// that set it first, which is the one mistake the "set it anywhere" contract invites.
var django_menus_repeat_click_ms = window.django_menus_repeat_click_ms || 0;

$(document).on('click', 'a.django-menus-item', function (event) {
    // An item's own data-django-menus-repeat-ms wins over the page's window, so a single item
    // can be held where the page has the guard off, and 0 on an item opts it out where the page
    // has it on. jQuery has already turned the attribute into a number.
    var item_ms = $(this).data('djangoMenusRepeatMs');
    // Number() so junk reads as off rather than as NaN comparisons that quietly never fire:
    // 0, a negative, a non-numeric string and true all fail this.
    var hold_ms = Number(item_ms === undefined ? django_menus_repeat_click_ms : item_ms);
    if (!(hold_ms > 0)) {
        return;
    }
    if (event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
        return;
    }
    // Something closer to the target has already cancelled the navigation - an inline onclick
    // returning false, an element-bound handler. Nothing was started, so there is nothing to
    // swallow, and arming here would eat the NEXT click: confirm() -> Cancel, then confirm() ->
    // OK within the window, and the user's confirmed click goes nowhere.
    if (event.isDefaultPrevented()) {
        return;
    }
    // Trimmed because a browser trims before deciding what a href means, so a scheme sitting
    // behind leading whitespace still counts as one.
    var href = ($(this).attr('href') || '').replace(/^\s+/, '');
    if (!href || href.charAt(0) === '#' || href.slice(0, 11).toLowerCase() === 'javascript:') {
        return;
    }
    // new Date().getTime() rather than Date.now(): the latter is ES5.1, and this file is served
    // as-is to whatever the project supports (django_menus declares no legacy_js build to fall
    // back to), so there is no reason for this to be what raises the browser floor.
    var now = new Date().getTime();
    var clicked_at = $(this).data('django-menus-clicked-at');
    if (clicked_at !== undefined && now - clicked_at < hold_ms) {
        // preventDefault alone, deliberately. `return false` would also stop propagation, and
        // jQuery runs directly-bound document handlers after delegated ones - so it would rob
        // the dropdown/context-menu closers and Bootstrap's clearMenus of a click they should
        // still see. Nothing here needs the click stopped, only the navigation.
        event.preventDefault();
        return;
    }
    $(this).data('django-menus-clicked-at', now);
});

$(window).on('pageshow', function (event) {
    // A page restored from the back/forward cache comes back with its jQuery data intact, so a
    // link clicked just before navigating away would still be held - clicking Back and
    // immediately clicking the same item again would do nothing. A restored page is a fresh
    // start, so the timers go.
    //
    // Nothing can be holding a timer unless something opted in, and this is the only place the
    // guard would touch the DOM while switched off, so it checks first: with no page-level
    // window and no item carrying its own, a restore does no work here.
    if (!event.originalEvent || !event.originalEvent.persisted) {
        return;
    }
    var held = $('a.django-menus-item[data-django-menus-repeat-ms]');
    if (Number(django_menus_repeat_click_ms) > 0) {
        held = $('a.django-menus-item');
    } else if (!held.length) {
        return;
    }
    held.removeData('django-menus-clicked-at');
});
