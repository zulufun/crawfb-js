async function get_posts() {
    resolve_all_links();
    click_more();

    let a_el_arr = Array.from(document.querySelectorAll('a')).filter(link => {
        let href = link.getAttribute('href');
        return href && (href.match(/\/(?:reel|posts|videos)\/[A-Za-z0-9:]+/) || href.match(/\/permalink\.php\?story_fbid=[A-Za-z0-9:]+&id=\d+/));
    }
    );

    let links_dict = {}

    for (let a_el of a_el_arr) {
        let link_match = a_el.href.match(/.*\/(reel|posts|videos)\/([A-Za-z0-9:]+)/)
        let link_match_posts_old = a_el.href.match(/.*\/permalink\.php\?story_fbid=([A-Za-z0-9:]+)&id=\d+/)
        let link_id = null
        let link_href = null
        let link_type = null

        if (link_match_posts_old) {
            link_id = link_match_posts_old[1]
            link_href = link_match_posts_old[0]
            link_type = "posts_old"
        } else if (link_match) {
            link_id = link_match[2]
            link_href = link_match[0]
            link_type = link_match[1]
        }

        switch (link_type) {
            case 'reel':
                break
            case 'videos':
                break
            case 'posts':
            case 'posts_old':
                try {
                    // Exclude comments
                    if (a_el.href.match(/.*\/(?:reel|posts|videos)\/[A-Za-z0-9:]+\/?\?comment_id=/)) {
                        continue;
                    }
                    // Exclude share posts
                    if (link_type == "posts" && !link_href.includes(window.location.href.split('/')[3])) {
                        continue;
                    }

                    if (link_type == "posts_old" && !link_href.includes(window.location.search.slice(1))) {
                        link_href = link_href.replace("permalink.php?story_fbid=", "story.php?id=")
                    }

                    if (link_href in links_dict)
                        continue;
                    let name = ""
                    let content = ""
                    let time = ""
                    try {
                        name = a_el.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.childNodes[0].querySelector("strong").innerText
                        // console.log(name)
                    } catch (e) {
                    }
                    try {
                        content = a_el.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.childNodes[2].innerText
                        // console.log(content)
                    } catch (e) {
                    }
                    try {
                        time = a_el.innerText
                        // console.log(time)
                    } catch (e) {
                    }
                    links_dict[link_id] = { link: link_href, content: content, name: name, time: time }
                } catch (e) {
                    console.log(a_el)
                }
                break
        }

    }
    return links_dict;
}

function resolve_all_links() {
    let eventFocusIn = new Event('focusin', {
        bubbles: true,
        cancelable: true
    });
    let eventFocusOut = new Event('focusout', {
        bubbles: true,
        cancelable: true
    });
    document.querySelectorAll('a').forEach(el => {
        el.dispatchEvent(eventFocusIn)
        el.dispatchEvent(eventFocusOut)
    }
    )

}

function click_more() {
    Array.from(document.querySelectorAll('div[role="button"][tabindex="0"].x1s688f'))
        .filter(div => div.textContent.trim() === atob("WGVtIHRo6m0="))
        .forEach(div => {
            // console.log(div)
            div.click();
        });
}

async function main() {
    let total_links = {};
    let anchor = 1000;
    window.scrollTo(0, anchor);
    for (let i = 0; i < 5; i++) {
        let links = await get_posts();
        total_links = { ...total_links, ...links };
        window.scrollTo(0, anchor + 500 * i);
        await new Promise(r => setTimeout(r, 1000));
    }

    console.log(total_links);
    return total_links;
}

return await main()
