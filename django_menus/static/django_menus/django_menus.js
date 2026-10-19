// Dropdowns are positioned by the vendored Floating UI (global FloatingUIDOM, so no clash with Bootstrap 4's Popper).

var MENU_VIEWPORT_PADDING = 8;  // context menus: keep clear of the viewport edge
var MENU_GAP = 2;

// Accepts an id, an element or (for custom templates written against the jQuery version) a jQuery object.
function menu_element(reference) {
    if (typeof reference === 'string') {
        return document.getElementById(reference);
    }
    if (reference && reference.jquery) {
        return reference[0];
    }
    return reference;
}

// Shows the menu and keeps it positioned until hide_menu; without Floating UI, Bootstrap's CSS places it.
function show_menu(reference, menu, placement) {
    menu.classList.add('show');
    if (typeof FloatingUIDOM === 'undefined') {
        return;
    }
    var fui = FloatingUIDOM;
    stop_positioning(menu);
    Object.assign(menu.style, {position: 'absolute', margin: '0', right: 'auto', bottom: 'auto'});
    menu._menu_cleanup = fui.autoUpdate(reference, menu, function () {
        fui.computePosition(reference, menu, {
            placement: placement,
            middleware: [fui.offset(MENU_GAP), fui.flip(), fui.shift()]
        }).then(function (pos) {
            menu.style.left = pos.x + 'px';
            menu.style.top = pos.y + 'px';
        });
    });
}

function stop_positioning(menu) {
    if (menu._menu_cleanup) {
        menu._menu_cleanup();
        menu._menu_cleanup = null;
    }
}

function hide_menu(menu) {
    menu.classList.remove('show', 'clicked');
    stop_positioning(menu);
}

function is_hovered(el) {
    return el.matches(':hover');
}

var dropdown_menu_function = function dropdown_menu_function(reference) {
    var placement = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'bottom-start';
    reference = menu_element(reference);
    var menu = document.getElementById(reference.id + '-menu');

    function hide_later(e) {
        setTimeout(function () {
            if (!is_hovered(reference) && !is_hovered(menu) && !menu.classList.contains('clicked')) {
                hide_menu(menu);
            }
        }, e.type === 'mouseleave' ? 300 : 0);
    }

    menu.addEventListener('click', function () {
        hide_menu(menu);
    });

    function reference_hover(e) {
        if (is_hovered(reference)) {
            document.querySelectorAll('.menu-system.show').forEach(function (el) {
                if (el !== menu) {
                    hide_menu(el);
                }
            });
            menu.classList.add('menu-system');
            show_menu(reference, menu, placement);
        }
        hide_later(e);
    }

    reference.addEventListener('mouseenter', reference_hover);
    reference.addEventListener('mouseleave', reference_hover);
    menu.addEventListener('mouseenter', hide_later);
    menu.addEventListener('mouseleave', hide_later);

    reference.addEventListener('click', function () {
        if (menu.classList.contains('clicked')) {
            hide_menu(menu);
        } else {
            menu.classList.add('clicked');
            show_menu(reference, menu, placement);
        }
    });

    reference.addEventListener('focusout', function () {
        if (menu.classList.contains('clicked') && !is_hovered(menu)) {
            hide_menu(menu);
        }
    });
};

var dropdown_menu_click = function dropdown_menu_click(reference) {
    var placement = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'bottom-start';
    reference = menu_element(reference);
    var menu = document.getElementById(reference.id + '-menu');

    menu.addEventListener('click', function () {
        if (menu.classList.contains('clicked')) {
            hide_menu(menu);
        }
    });

    reference.addEventListener('click', function () {
        if (menu.classList.contains('clicked')) {
            hide_menu(menu);
        } else {
            menu.classList.add('clicked');
            show_menu(reference, menu, placement);
        }
    });

    reference.addEventListener('focusout', function () {
        if (menu.classList.contains('clicked') && !is_hovered(menu)) {
            hide_menu(menu);
        }
    });
};


function click_href(href) {
    var a = document.createElement('a');
    a.style.display = 'none';
    a.href = href;
    document.body.appendChild(a);
    a.click();
    a.remove();
}


ajax_helpers.command_functions.enable_context_menu = function (command) {
    // Delegated, so elements added after page load get the menu too.
    document.addEventListener('contextmenu', function (evt) {
        var el = evt.target.closest ? evt.target.closest(command.selector) : null;
        if (!el) {
            return;
        }
        evt.preventDefault();

        // Create a dictionary (object) to store data attributes and id
        var elementData = {'ajax': 'context_menu', 'pos': [evt.pageX, evt.pageY]};
        elementData['id'] = el.id;

        // Get all data attributes and add them to the dictionary
        Object.assign(elementData, el.dataset);
        ajax_helpers.event = evt;
        ajax_helpers.post_json({'data': elementData});
    });
};


// Replaces #context-menu (or appends to body) with html. Scripts are re-created because innerHTML does not
// run them, and nested dropdowns in the menu html set themselves up with a <script>.
function insert_context_menu(html) {
    var old = document.getElementById('context-menu');
    var tmp = document.createElement('div');
    tmp.innerHTML = html;
    var nodes = Array.prototype.slice.call(tmp.childNodes);
    nodes.forEach(function (node) {
        if (old) {
            old.parentNode.insertBefore(node, old);
        } else {
            document.body.appendChild(node);
        }
    });
    if (old) {
        old.remove();
    }
    nodes.forEach(function (node) {
        if (node.nodeType !== 1) {
            return;
        }
        var scripts = node.tagName === 'SCRIPT' ? [node] : Array.prototype.slice.call(node.querySelectorAll('script'));
        scripts.forEach(function (script) {
            var fresh = document.createElement('script');
            fresh.text = script.textContent;
            script.parentNode.replaceChild(fresh, script);
        });
    });
}


var context_menu_outside_click;

ajax_helpers.command_functions.context_menu = function (command) {
    insert_context_menu(command.menu);
    var menu = document.getElementById('context-menu');

    // Ensure the menu is valid before proceeding
    if (!menu) {
        console.error('Dropdown menu not found');
        return;
    }

    // Get the viewport bounds in document coordinates. Context-menu events already
    // provide page coordinates, and AJAX dropdowns send document coordinates below.
    var windowWidth = document.documentElement.clientWidth;
    var windowHeight = document.documentElement.clientHeight;
    var viewportLeft = window.scrollX;
    var viewportTop = window.scrollY;
    var viewportRight = viewportLeft + windowWidth;
    var viewportBottom = viewportTop + windowHeight;

    // Measure while displayed; a hidden menu has no size.
    menu.style.display = 'block';
    var menuWidth = menu.offsetWidth;
    var menuHeight = menu.offsetHeight;

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
    var viewportPadding = MENU_VIEWPORT_PADDING;
    if (menuHeight > windowHeight - (viewportPadding * 2)) {
        menu.style.maxHeight = (windowHeight - (viewportPadding * 2)) + 'px';
        menu.style.overflowY = 'auto';
        menuHeight = menu.offsetHeight;
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
    menu.style.top = positionY + 'px';
    menu.style.left = positionX + 'px';

    // Hide the menu when clicking outside of it
    if (context_menu_outside_click) {
        document.removeEventListener('click', context_menu_outside_click);
    }
    context_menu_outside_click = function (e) {
        if (!menu.contains(e.target)) {
            menu.style.display = 'none';
            // Remove the click event handler after hiding the menu
            document.removeEventListener('click', context_menu_outside_click);
            context_menu_outside_click = null;
        }
    };
    document.addEventListener('click', context_menu_outside_click);

    // Hides the menu as soon as you clicked it
    menu.addEventListener('click', function () {
        menu.style.display = 'none';
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
