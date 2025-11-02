// Biến lưu trữ tất cả logs
let logBuffer = [];

// Hàm thêm log vào buffer
function addLog(message, data = {}) {
    const timestamp = new Date().toISOString();
    const logEntry = {
        timestamp,
        message,
        data
    };
    logBuffer.push(logEntry);
    console.log(`[LOG] ${message}`, data);
}

/**
 * Hàm lấy tên người đăng bài từ element link
 */
function getPostAuthorName(a_el) {
    try {
        // Phương pháp 1: Tìm strong tag gần nhất
        let currentElement = a_el;
        let maxDepth = 15;
        
        for (let i = 0; i < maxDepth; i++) {
            if (!currentElement.parentNode) break;
            currentElement = currentElement.parentNode;
            
            let strongTag = currentElement.querySelector('strong');
            if (strongTag && strongTag.innerText && strongTag.innerText.trim()) {
                let name = strongTag.innerText.trim();
                if (name.length > 0 && name.length < 100) {
                    return name;
                }
            }
        }
        
        currentElement = a_el;
        for (let i = 0; i < maxDepth; i++) {
            if (!currentElement.parentNode) break;
            currentElement = currentElement.parentNode;
            
            let profileLink = currentElement.querySelector('a[aria-label*="profile"]');
            if (profileLink) {
                let ariaLabel = profileLink.getAttribute('aria-label');
                if (ariaLabel) {
                    let nameMatch = ariaLabel.match(/^(.+?)(?:'s profile| profile)/i);
                    if (nameMatch && nameMatch[1]) {
                        return nameMatch[1].trim();
                    }
                }
            }
        }
        
        currentElement = a_el;
        for (let i = 0; i < maxDepth; i++) {
            if (!currentElement.parentNode) break;
            currentElement = currentElement.parentNode;
            
            let headingTags = currentElement.querySelectorAll('h2, h3, h4');
            for (let heading of headingTags) {
                let name = heading.innerText.trim();
                if (name.length > 0 && name.length < 100) {
                    return name;
                }
            }
        }
        
    } catch (e) {
        console.error("Error in getPostAuthorName:", e);
    }
    
    return "";
}

async function get_posts() {
    resolve_all_links();
    click_more();

    let a_el_arr = Array.from(document.querySelectorAll('a')).filter(link => {
        let href = link.getAttribute('href');
        return href && (href.match(/\/(?:reel|posts|videos)\/[A-Za-z0-9:]+/) || href.match(/\/permalink\.php\?story_fbid=[A-Za-z0-9:]+&id=\d+/));
    });

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
                        // SỬ DỤNG HÀM MỚI ĐỂ LẤY TÊN
                        name = getPostAuthorName(a_el);
                        
                        // GHI LOG CHI TIẾT
                        addLog(`Name extracted: ${name}`, {
                            name: name,
                            link_id: link_id,
                            link_href: link_href,
                            link_type: link_type,
                            a_el_info: {
                                href: a_el.href,
                                innerText: a_el.innerText,
                                className: a_el.className,
                                id: a_el.id,
                                tagName: a_el.tagName,
                                outerHTML: a_el.outerHTML.substring(0, 200)
                            }
                        });
                        
                    } catch (e) {
                        addLog(`Failed to extract name`, {
                            error: e.message,
                            link_id: link_id,
                            link_href: link_href,
                            a_el_info: {
                                href: a_el.href,
                                innerText: a_el.innerText
                            }
                        });
                        console.log(e);
                    }
                    
                    try {
                        content = a_el.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.childNodes[2].innerText
                    } catch (e) {
                    }
                    
                    try {
                        time = a_el.innerText
                    } catch (e) {
                    }
                    
                    links_dict[link_id] = { link: link_href, content: content, name: name, time: time }
                } catch (e) {
                    // console.log(a_el)
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
    });
}

function click_more() {
    Array.from(document.querySelectorAll('div[role="button"][tabindex="0"].x1s688f'))
        .filter(div => div.textContent.trim() === atob("WGVtIHRo6m0="))
        .forEach(div => {
            div.click();
        });
}

async function main() {
    let total_links = {};
    let anchor = 1000;
    window.scrollTo(0, anchor);
    
    for (let i = 0; i < 5; i++) {
        addLog(`Starting iteration ${i + 1}/5`, { scroll_position: anchor + 500 * i });
        
        let links = await get_posts();
        total_links = { ...total_links, ...links };
        
        addLog(`Iteration ${i + 1} completed`, { 
            links_found: Object.keys(links).length,
            total_links_so_far: Object.keys(total_links).length 
        });
        
        window.scrollTo(0, anchor + 500 * i);
        await new Promise(r => setTimeout(r, 1000));
    }

    console.log(total_links);
    
    addLog(`Scraping completed`, { 
        total_links: Object.keys(total_links).length
    });
    
    // Trả về cả links và logs để Python xử lý
    return {
        links: total_links,
        logs: logBuffer
    };
}

return await main()