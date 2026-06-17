#!/usr/bin/env python3
import re

path = r"C:\Users\LYS\.qclaw\workspace\embedded-dev-site\static\index.html"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add "time" field to each cardsData entry
# Replace: , size:'112KB' → , time:'~60分钟', size:'112KB'
time_map = {
    "main": "~60分钟", "arm-gcc": "~20分钟", "cmake": "~20分钟",
    "makefile": "~25分钟", "flash-debug": "~30分钟", "serial": "~20分钟",
    "stm32": "~35分钟", "esp32": "~20分钟", "freertos": "~40分钟",
    "protocols": "~20分钟", "practice-projects": "~10分钟", "bci-2026": "~15分钟",
    "proj-led-button": "~15分钟", "proj-uart-hello": "~15分钟",
    "proj-oled-display": "~15分钟", "proj-dht11-monitor": "~12分钟",
    "proj-pwm-motor": "~18分钟", "proj-servo-control": "~18分钟",
    "proj-ir-remote": "~15分钟", "proj-ultrasonic": "~15分钟",
    "proj-stepper-motor": "~18分钟", "proj-freertos-station": "~20分钟",
    "proj-smart-car": "~25分钟", "proj-can-bus": "~20分钟",
    "proj-sd-logger": "~20分钟", "proj-esp32-iot": "~20分钟",
    "proj-low-power": "~18分钟", "proj-bootloader-iap": "~20分钟",
    "proj-dma-adc": "~18分钟", "proj-usb-hid": "~20分钟",
    "proj-s32k144-auto": "~20分钟", "proj-oscilloscope-debug": "~15分钟"
}

for page_id, time_val in time_map.items():
    # Match: page:'xxx', ... other fields ... but before size:
    pattern = rf"(page:'{page_id}',[^}}]*?), size:"
    replacement = rf"\1, time:'{time_val}', size:"
    content = re.sub(pattern, replacement, content)

# 2. Update card rendering to show time
content = content.replace(
    "<div class=\"size\">${c.size}</div>",
    "<div class=\"size\">${c.size} <span class=\"read-time\">⏱ ${c.time||''}</span></div>"
)

# 3. Add sort bar before home-grid rendering
old_sort = "function renderCardGroup(title, items) {"
new_sort_block = """let sortMode = 'default';
function renderSortBar() {
  return `<div class="sort-bar"><span class="label">排序：</span>
    <button class="sort-btn active" onclick="sortCards('default',this)">默认</button>
    <button class="sort-btn" onclick="sortCards('time-asc',this)">⏱ 短→长</button>
    <button class="sort-btn" onclick="sortCards('time-desc',this)">⏱ 长→短</button>
    <button class="sort-btn" onclick="sortCards('diff-asc',this)">📊 简单→难</button>
    <button class="sort-btn" onclick="sortCards('name',this)">🔤 名称</button>
  </div>`;
}
function sortCards(mode, btn) {
  document.querySelectorAll('.sort-btn').forEach(b=>b.classList.remove('active'));
  if(btn) btn.classList.add('active');
  sortMode = mode;
  loadPage('home');
}
function getSorted(items) {
  if (sortMode === 'time-asc') return [...items].sort((a,b)=>parseInt(a.time||'99')-parseInt(b.time||'99'));
  if (sortMode === 'time-desc') return [...items].sort((a,b)=>parseInt(b.time||'99')-parseInt(a.time||'99'));
  if (sortMode === 'diff-asc') return [...items].sort((a,b)=>(a.diff||0)-(b.diff||0));
  if (sortMode === 'name') return [...items].sort((a,b)=>a.title.localeCompare(b.title,'zh'));
  return items;
}
function renderCardGroup(title, items) {
  items = getSorted(items);"""

content = content.replace(old_sort, new_sort_block)

# 4. Add sort bar after home-stats div in renderHome
old_stats_end = "`;</div>`;\n\n  // 分组"
if old_stats_end in content:
    content = content.replace(
        old_stats_end,
        "`;</div>`;\n\n  html += renderSortBar();\n\n  // 分组"
    )

# 5. Add bookmark JS functions before // === 初始化 ===
bookmark_js = """// === 收藏夹 ===
function getBookmarks() {
  try { return JSON.parse(localStorage.getItem('tutorial_bookmarks')||'[]'); }
  catch(e) { return []; }
}
function saveBookmarks(list) { localStorage.setItem('tutorial_bookmarks', JSON.stringify(list)); }
function toggleBookmark(pageId) {
  const bm = getBookmarks();
  const idx = bm.indexOf(pageId);
  if (idx >= 0) bm.splice(idx, 1);
  else bm.push(pageId);
  saveBookmarks(bm);
  updateBookmarkUI();
  renderBookmarksList();
}
function isBookmarked(pageId) { return getBookmarks().includes(pageId); }
function updateBookmarkUI() {
  const btn = document.getElementById('bmToggle');
  if (!btn) return;
  if (isBookmarked(currentPage)) { btn.classList.add('active'); btn.textContent = '⭐'; }
  else { btn.classList.remove('active'); btn.textContent = '☆'; }
}
function renderBookmarksList() {
  const bm = getBookmarks();
  const section = document.getElementById('bookmarksSection');
  const list = document.getElementById('bookmarkList');
  const countEl = document.getElementById('bmCount');
  if (bm.length === 0) { section.style.display = 'none'; return; }
  section.style.display = 'block';
  countEl.textContent = bm.length;
  let html = '';
  bm.forEach(id => {
    const cfg = PAGES[id];
    if (cfg) html += `<div class="bm-item" onclick="loadPage('${id}')">${cfg.title}<span class="bm-remove" onclick="event.stopPropagation();removeBookmark('${id}')">✕</span></div>`;
  });
  list.innerHTML = html;
}
function removeBookmark(pageId) {
  const bm = getBookmarks().filter(id => id !== pageId);
  saveBookmarks(bm);
  renderBookmarksList();
  updateBookmarkUI();
}

// === 学习进度 ===
function markViewed(pageId) {
  if (pageId === 'home') return;
  try {
    const viewed = JSON.parse(localStorage.getItem('tutorial_viewed')||'{}');
    viewed[pageId] = new Date().toISOString();
    localStorage.setItem('tutorial_viewed', JSON.stringify(viewed));
  } catch(e) {}
}
function getViewedCount() {
  try { return Object.keys(JSON.parse(localStorage.getItem('tutorial_viewed')||'{}')).length; }
  catch(e) { return 0; }
}
function getProgressPercent() {
  const total = Object.keys(PAGES).length - 1; // exclude home
  return Math.round((getViewedCount() / total) * 100);
}
function progressIndicator() {
  const pct = getProgressPercent();
  return pct > 0 ? `<div class="progress-indicator" title="已读 ${pct}%"><div class="pi-bar"><div class="pi-fill" style="width:${pct}%"></div></div>${pct}%</div>` : '';
}
function updateHomeStats() {
  const viewed = getViewedCount();
  const progressHtml = progressIndicator();
  // Update stats if on home page
  const statsDiv = document.querySelector('.home-stats');
  if (statsDiv) {
    const existing = statsDiv.querySelector('.home-stat.progress-stat');
    if (!existing && viewed > 0) {
      const statEl = document.createElement('div');
      statEl.className = 'home-stat progress-stat';
      statEl.innerHTML = `<div class="num">${viewed}</div><div class="label">已学习</div><div class="progress-indicator" style="margin-top:4px"><div class="pi-bar"><div class="pi-fill" style="width:${getProgressPercent()}%"></div></div>${getProgressPercent()}%</div>`;
      statsDiv.appendChild(statEl);
    } else if (existing && viewed > 0) {
      existing.querySelector('.num').textContent = viewed;
      existing.querySelector('.pi-fill').style.width = getProgressPercent()+'%';
      existing.querySelector('.progress-indicator').childNodes[2].textContent = getProgressPercent()+'%';
    }
  }
}

"""

insert_at = "// === 初始化 ==="
content = content.replace(insert_at, bookmark_js + "\n" + insert_at)

# 6. Update loadPage to add bookmark button, mark viewed, and render bookmarks list
# Add bookmark button after breadcrumb update
old_bm = "// 关闭移动端侧边栏\n  document.getElementById('sidebar').classList.remove('open');"
new_bm = """// 关闭移动端侧边栏
  document.getElementById('sidebar').classList.remove('open');

  // 更新收藏按钮
  const bmToggle = document.getElementById('bmToggle');
  if (bmToggle) {
    if (pageId === 'home') { bmToggle.style.display = 'none'; }
    else { bmToggle.style.display = ''; updateBookmarkUI(); }
  }

  // 标记已读
  if (pageId !== 'home') markViewed(pageId);"""
content = content.replace(old_bm, new_bm)

# 7. Add bookmark toggle button in topbar (after search-box)
old_search = '<input type="text" id="searchInput" placeholder="搜索教程内容..." oninput="handleSearch(this.value)">\n    </div>'
new_search = '<input type="text" id="searchInput" placeholder="搜索教程内容..." oninput="handleSearch(this.value)">\n    </div>\n    <button class="bookmark-btn" id="bmToggle" onclick="toggleBookmark(currentPage)" title="收藏当前教程" style="display:none">☆</button>'
content = content.replace(old_search, new_search)

# 8. Update init to load bookmarks
old_init = "loadPage('home');"
new_init = "loadPage('home');\n  renderBookmarksList();\n  updateHomeStats();"
content = content.replace(old_init, new_init)

# 9. Add renderBookmarksList + updateHomeStats calls in loadPage for home
old_home_return = "history.pushState({page:pageId}, '', `#/${pageId}`);\n    return;"
new_home_return = "history.pushState({page:pageId}, '', `#/${pageId}`);\n    updateHomeStats();\n    setTimeout(() => updateHomeStats(), 200);\n    return;"
content = content.replace(old_home_return, new_home_return)

# 10. After tutorial loads, call updateBookmarkUI and show bookmark button
old_postload = "content.appendChild(navHtml);"
new_postload = "content.appendChild(navHtml);\n    // 显示收藏按钮\n    const bmBtn = document.getElementById('bmToggle');\n    if (bmBtn) { bmBtn.style.display = ''; updateBookmarkUI(); }"
content = content.replace(old_postload, new_postload)

with open(path, 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("Done! Statistics:")
print(f"  Total chars: {len(content)}")
print(f"  Has bookmark JS: {'getBookmarks' in content}")
print(f"  Has time fields: {'time:' in content}")
print(f"  Has sort bar: {'renderSortBar' in content}")
print(f"  Has bmToggle: {'bmToggle' in content}")
print(f"  Has markViewed: {'markViewed' in content}")
