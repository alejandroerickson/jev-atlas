// Local change (atlas shim): an arrow function, not an invoked one. Python calls it
// with the selector lists -- the harness defaults plus whatever the atlas appends --
// so nothing application-specific has to be written into this file.
((SELECTORS) => {
  if (!document.body) return null;
  const SEL = SELECTORS || {};
  const cache = window.__jevFast ||= {ids:new WeakMap(), nodes:new Map(), next:1};
  const identity = e => {
    if (!cache.ids.has(e)) cache.ids.set(e,cache.next++);
    const id=cache.ids.get(e); cache.nodes.set(id,e); return id;
  };
  for (const [id,e] of cache.nodes) if (!e.isConnected) cache.nodes.delete(id);
  const safe = e => !['password','file','hidden'].includes(e.type);
  const visible = e => !e.closest('[aria-hidden="true"],[inert]') &&
    e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
  const name = (e,seen=new Set()) => {
    if (!e || seen.has(e)) return '';
    seen.add(e);
    const referenced=(e.getAttribute('aria-labelledby')||'').split(/\s+/)
      .map(id=>name(document.getElementById(id),seen)).filter(Boolean).join(' ');
    return referenced || e.getAttribute('aria-label') ||
      [...(e.labels||[])].map(l=>name(l,seen)).filter(Boolean).join(' ') ||
      (['button','submit','reset'].includes(e.type) ? e.value : '') || e.getAttribute('alt') ||
      (e.tagName==='INPUT' ? '' : [...e.childNodes].map(n=>n.nodeType===3 ? n.textContent :
        n.nodeType===1 && n.getAttribute('aria-hidden')!=='true' ? name(n,seen) : '').join(' ').trim()) ||
      e.getAttribute('title') || e.getAttribute('placeholder') || '';
  };
  // Local change (atlas shim): stable keys and states per element, sent as fields.
  // The label is untouched; Python looks these up in an application atlas.
  // Injected: jev_ultrafast/atlas.py's DEFAULT_DIALOG and DEFAULT_BUSY, plus the
  // atlas's own `selectors` entries. Which entries are application-specific, and
  // why they are defaults rather than atlas entries, is documented there.
  // `:not(*)` is valid CSS that matches nothing, so an empty list reads as "none of
  // these exist here" instead of throwing a SyntaxError out of every query.
  const DIALOG=(SEL.dialog||[]).join(',')||':not(*)';
  const BUSY=(SEL.busy||[]).join(',')||':not(*)';
  // What counts as a busy indicator when it is the thing covering a control:
  // a custom element such as <app-busy-indicator> is a tag name, which no class
  // selector would find.
  const BUSYISH=/busy|loading|spinner|progress/i;
  const ancestorTag = e => {
    for (let p=e.parentElement; p; p=p.parentElement)
      if (p.tagName.includes('-')) return p.tagName.toLowerCase();
    return null;
  };
  const hrefPath = e => {
    const raw=e.getAttribute('href');
    if (raw===null) return null;
    // Local change: a hash-routed application keeps its route in the fragment, so a
    // fragment that reads as a route ('#/…' or '#!/…') stays; an in-page anchor such
    // as '#content' does not, and neither does anything else after the '#'.
    try {
      const u=new URL(raw,location.href);
      return u.pathname+u.search+(/^#!?\//.test(u.hash) ? u.hash : '');
    } catch { return raw; }
  };
  // Local change: the nearest landmark around an element, as its ARIA role plus its
  // accessible name when it has one ("navigation: Breadcrumb"), so a top-bar link and a
  // same-named page link can be told apart. <header>/<footer> count as banner and
  // contentinfo wherever they are (a simplification of the ARIA scoping rule).
  const LANDMARK_TAGS={NAV:'navigation',HEADER:'banner',MAIN:'main',ASIDE:'complementary',
    FOOTER:'contentinfo',SEARCH:'search'};
  const LANDMARK_ROLES=['navigation','banner','main','complementary','contentinfo','search','region','form'];
  const landmarkOf = e => {
    for (let p=e.parentElement; p && p!==document.body; p=p.parentElement) {
      const explicit=p.getAttribute('role');
      const kind=LANDMARK_ROLES.includes(explicit) ? explicit : LANDMARK_TAGS[p.tagName];
      if (!kind) continue;
      const label=(p.getAttribute('aria-labelledby') ? name(p) : p.getAttribute('aria-label')) || '';
      // A region or form is a landmark only when it is named.
      if ((kind==='region' || kind==='form') && !label.trim()) continue;
      const tidyLabel=label.trim().replace(/\s+/g,' ').slice(0,80);
      return tidyLabel ? kind+': '+tidyLabel : kind;
    }
    return null;
  };
  // Covered: something else owns the element's centre, so a click cannot reach it.
  // Returns what is in the way, so a run log can say whether it was a dialog or a
  // loading mask that hid the control.
  const describe = e => e ? e.tagName.toLowerCase() +
    ((e.className||'')+'').trim().split(/\s+/).filter(Boolean).slice(0,2).map(c=>'.'+c).join('') : 'nothing';
  const coveredAt = (e,x,y) => {
    try {
      const top=document.elementFromPoint(x,y);
      return (top===e || e.contains(top) || (top && top.contains(e))) ? null : describe(top);
    } catch { return null; }
  };
  const clean = e => e ? (e.innerText||e.textContent||'').trim().replace(/\s+/g,' ') : '';
  const roles=['button','link','checkbox','radio','switch','tab','menuitem','menuitemradio',
    'option','gridcell','combobox','textbox','searchbox','spinbutton'];
  const selector='a[href],button,input,textarea,select,summary,[contenteditable="true"],'+
    roles.map(role=>'[role="'+role+'"]').join(',');
  const TEMPORAL=['date','time','datetime-local','month','week'];
  const role = e => {
    const explicit=e.getAttribute('role');
    if (roles.includes(explicit)) return explicit;
    if (e.tagName==='BUTTON' || e.tagName==='SUMMARY') return 'button';
    if (e.tagName==='A') return 'link';
    if (e.tagName==='SELECT') return 'combobox';
    if (e.tagName==='TEXTAREA' || e.isContentEditable) return 'textbox';
    if (e.tagName==='INPUT') {
      if (['checkbox','radio'].includes(e.type)) return e.type;
      if (['button','submit','reset','image'].includes(e.type)) return 'button';
      if (e.type==='search') return 'searchbox';
      if (e.type==='number') return 'spinbutton';
      if (['text','email','url','tel'].includes(e.type)) return 'textbox';
      // Local change: date and time pickers are typed into like any field; the
      // executor writes them through the native value setter (see browser.py).
      if (TEMPORAL.includes(e.type)) return 'textbox';
    }
    return null;
  };
  cache.pageKey=()=>[performance.timeOrigin,location.href,scrollX,scrollY,innerWidth,innerHeight,
    [...document.querySelectorAll('input,textarea,select')].filter(safe)
      .map(e=>[identity(e),e.value,e.checked,e.selectedIndex,e.disabled,e.readOnly])];
  cache.guard=e=>{
    if (!e?.isConnected || !visible(e)) return null;
    const scope=e.closest('form,dialog,[role="dialog"],article,li,tr,[role="row"]') || e.parentElement;
    return [identity(e),role(e),name(e),e.value??null,e.checked??null,e.selectedIndex??null,
      e.readOnly??null,e.matches(':disabled'),e.getAttribute('aria-disabled'),
      e.getAttribute('aria-expanded'),e.getAttribute('aria-checked'),e.getAttribute('aria-selected'),
      e.getAttribute('href'),scope?.innerText?.slice(0,6000)||''];
  };
  // Local change: a form widget with no accessible name borrows the label of its
  // own row, so a library combobox reads as "Colour" instead of "combobox"
  // — and does not rename itself to its own value once it is filled.
  const LABELISH='label,[class*="label"],th';
  const GENERIC=new Set(['','combobox','select','listbox','textbox','searchbox','spinbutton','input','textarea']);
  const INLINE=new Set(['SPAN','EM','I','B','U','A','LABEL','STRONG','SMALL','FONT']);
  const flat = e => (e.textContent||'').replace(/[\uE000-\uF8FF]/g,'').replace(/\s+/g,' ').trim();
  const short = e => { const t=flat(e); return t && t.length<=60 ? t : ''; };
  const tidy = t => t.replace(/(\s*[:*])+\s*$/,'').trim();
  // Local change: a <label> that belongs to another control is that control's name,
  // not a row label for this one: a header button must not borrow a comment box's
  // label, nor a radio its sibling radio's.
  const ownedElsewhere = (l,e) => l.tagName==='LABEL' && l.control && l.control!==e;
  // Local change: a control in a table row takes the row's identifying cells. The
  // first cell is enough when it is unique among its sibling rows; when it is not
  // (a status column: "selected" on every row) the next cells are added, up to
  // three, until it is. A row header (th[scope=row], role=rowheader) wins outright.
  const CELLS=':scope > td, :scope > th, :scope > [role="cell"], :scope > [role="gridcell"], :scope > [role="rowheader"]';
  const cellTexts = (row,e) => [...row.querySelectorAll(CELLS)]
    .filter(c=>!(e && c.contains(e)) && !c.matches(selector) && !c.querySelector(selector) && short(c))
    .map(c=>tidy(flat(c)));
  const tableRows=new Map();
  const rowSummary = (row,e) => {
    const header=[...row.querySelectorAll(':scope > th[scope="row"], :scope > [role="rowheader"]')]
      .find(c=>!c.contains(e) && short(c));
    if (header) return tidy(flat(header));
    const mine=cellTexts(row,e);
    if (!mine.length) return null;
    const siblings=[...(row.parentElement?.children||[])].filter(r=>r!==row).map(r=>cellTexts(r,null));
    for (let n=1; n<=Math.min(3,mine.length); n++) {
      const key=mine.slice(0,n).join(' · ');
      if (n===Math.min(3,mine.length) || !siblings.some(s=>s.slice(0,n).join(' · ')===key)) return key;
    }
    return mine[0];
  };
  // Local change: repeated structure. The items of a list share a tag and first
  // class; a flat grid (each line several sibling cells, the lines one after
  // another in one container) repeats a short sequence of them. Either way, the
  // container's first child belongs to one item, not to all of them.
  const sig = e => e.tagName+'.'+((e.getAttribute('class')||'').trim().split(/\s+/)[0]||'');
  const periods=new Map();
  const periodOf = p => {
    if (periods.has(p)) return periods.get(p);
    const kids=[...p.children].map(sig), n=kids.length;
    let found=0;
    for (let k=2; k<=8 && 2*k<=n && !found; k++) {
      if (new Set(kids.slice(0,k)).size<2) continue;
      let ok=true;
      for (let i=k; i<n && ok; i++) ok=kids[i]===kids[i%k];
      if (ok) found=k;
    }
    periods.set(p,found);
    return found;
  };
  // The line of a flat grid that `child` belongs to, or null when `p` is not one.
  const lineOf = (p,child) => {
    const k=p && periodOf(p);
    if (!k) return null;
    const kids=[...p.children], i=kids.indexOf(child);
    if (i<0) return null;
    return kids.slice(i-i%k, i-i%k+k);
  };
  // The other items `child` is repeated with inside `p` (same tag and first class).
  const repeatedWith = (p,child) => {
    const s=sig(child);
    return [...p.children].filter(c=>c!==child && sig(c)===s);
  };
  const rows=new Map();
  const rowLabel = e => {
    const start=e.parentElement;
    if (!start) return null;
    if (rows.has(start)) return rows.get(start);
    let found=null, levels=0;
    for (let node=start, prev=e, steps=0; node && node!==document.body && steps<10;
         prev=node, node=node.parentElement, steps++) {
      // Inline wrappers and component elements are not rows; only ordinary block
      // ancestors count towards the four, or a widget's own chrome exhausts them.
      if (!INLINE.has(node.tagName) && !node.tagName.includes('-') && ++levels>4) break;
      // Local change: stop at a landmark; a label found beyond it belongs to another part of the page.
      if (node!==start && (LANDMARK_TAGS[node.tagName] || LANDMARK_ROLES.includes(node.getAttribute('role')))) break;
      // Local change: in a flat grid the row label is the first cell of this
      // control's own line. The container's first child is the FIRST line's cell,
      // which put one line's "Approval overdue" on every line of a ledger.
      const line=lineOf(node,prev);
      if (line) {
        const head=line[0];
        found=!head.contains(e) && short(head) && !head.matches(selector) && !head.querySelector(selector) ?
          tidy(flat(head)) : null;
        break;
      }
      // Likewise, a label inside a sibling item of a list is that item's, not this one's.
      // (Every cell of a table row is one of its items, whatever its class.)
      const others=node.matches('tr,[role="row"]') ? [...node.children].filter(c=>c!==prev) : repeatedWith(node,prev);
      const mine=l=>!others.some(o=>o.contains(l));
      let found_here=[...node.querySelectorAll(LABELISH)].filter(l=>!l.contains(e) && short(l) &&
        !ownedElsewhere(l,e) && mine(l));
      // A header row names columns, not a row: its cells are nobody's row label.
      if (!found_here.length && node.matches('tr,[role="row"]') && !node.closest('thead') &&
          !node.querySelector(':scope > th[scope="col"], :scope > [role="columnheader"]')) {
        if (!tableRows.has(node)) tableRows.set(node,rowSummary(node,e));
        const summary=tableRows.get(node);
        if (summary) { found=summary; break; }
      }
      if (!found_here.length) {
        const first=node.firstElementChild;
        found_here=first && !first.contains(e) && mine(first) && short(first) &&
          !first.matches(selector) && !first.querySelector(selector) ? [first] : [];
      } else if (found_here.length>1) {
        // Several labels in one container: only the one in its first cell is the row's.
        const first=node.firstElementChild;
        found_here=first ? found_here.filter(l=>l===first || first.contains(l)) : [];
      }
      if (found_here.length===1) { found=tidy(flat(found_here[0])); break; }
      if (found_here.length>1) break;
    }
    rows.set(start,found||null);
    return found||null;
  };
  // Local change: the identifying line of the row, list item or card a control
  // sits in, so "Open" on every card, or a link whose text is only an id
  // ("WF-2026-0146"), can be told apart. Up to three pieces of the row's own text
  // -- its other cells, or the other blocks of its item -- in page order, joined by
  // " · ": typically the title and a short status. Left out: the control's own
  // text, blocks holding a button or a field, and the control's peers (the other
  // items of a list, tab strip or button bar it belongs to). Links are kept,
  // because a row's title is often one. A table row counts (a header row never
  // does); so does a line of a flat grid, and any other list item or repeated
  // block when it is small: at most three controls besides the peers, and 400
  // characters, so a whole column of cards is not taken for a row.
  const ROWISH='li,[role="listitem"],article,[role="article"]';
  const FIELDISH='button,input,select,textarea,[role="button"],[role="checkbox"],[role="radio"],'+
    '[role="switch"],[role="combobox"],[role="textbox"],[role="searchbox"],[role="spinbutton"],[contenteditable="true"]';
  const HEADER_ROW=':scope > th[scope="col"], :scope > [role="columnheader"]';
  // Text with a space between separate text nodes: "costed 2026-11-30", not "costed2026-11-30".
  const spaced = el => {
    const out=[], walk=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
    for (let n; (n=walk.nextNode());) if (n.textContent.trim()) out.push(n.textContent);
    return out.join(' ').replace(/[\uE000-\uF8FF]/g,'').replace(/\s+/g,' ').trim();
  };
  const piece = t => t.length>80 ? t.slice(0,79)+'…' : t;
  const rowContext = (e,tableOnly) => {
    const own=tidy(spaced(e)), peers=[];
    const isPeer = el => peers.some(p=>p===el || p.contains(el));
    for (let node=e.parentElement, prev=e, steps=0; node && node!==document.body && steps<8;
         prev=node, node=node.parentElement, steps++) {
      if (node.matches(DIALOG) || LANDMARK_TAGS[node.tagName] || LANDMARK_ROLES.includes(node.getAttribute('role'))) break;
      const parent=node.parentElement, line=lineOf(parent,node);
      const table=!line && node.matches('tr,[role="row"]');
      if (table && (node.closest('thead') || node.querySelector(HEADER_ROW))) return null;
      // Items repeated beside the path that hold controls are this control's peers.
      if (!node.matches('tr,[role="row"]') && !lineOf(node,prev))
        peers.push(...repeatedWith(node,prev).filter(c=>c.matches(selector) || c.querySelector(selector)));
      let parts=null;
      if (line) parts=line;
      else if (table) parts=[...node.querySelectorAll(CELLS)];
      else if (node.matches(ROWISH) || (parent && repeatedWith(parent,node).length)) parts=[node];
      if (!parts || (tableOnly && !table)) {
        if (node.matches('table,[role="table"],[role="grid"],form')) break;
        continue;
      }
      if (!table) {
        const controls=new Set();
        for (const p of parts) for (const c of [p, ...p.querySelectorAll(selector)])
          if (c.matches(selector) && !isPeer(c)) controls.add(c);
        if (controls.size>3 || parts.map(flat).join(' ').length>400) return null;
      }
      const pieces=[];
      // Inside a card, the items of some other list (a column's tickets under its
      // head) are not this row's text; a table row's cells and a grid's line are.
      const listItem = el => !table && !line && el.parentElement && repeatedWith(el.parentElement,el).length &&
        (el.matches(selector) || el.querySelector(selector));
      const add = el => {
        if (el===e || isPeer(el) || el.matches(FIELDISH) || el.querySelector(FIELDISH) || listItem(el)) return;
        const t=tidy(spaced(el));
        if (t && t!==own && /[\p{L}\p{N}]/u.test(t) && !pieces.includes(t)) pieces.push(t);
      };
      const expand = el => {
        if (el===e || isPeer(el)) return;
        if (el.contains(e) || peers.some(p=>el.contains(p))) { for (const c of el.children) expand(c); return; }
        add(el);
      };
      if (table) parts.filter(c=>!c.contains(e)).forEach(add);
      else parts.forEach(expand);
      if (pieces.length) return pieces.slice(0,3).map(piece).join(' · ');
      // A table row with nothing else in it, or a line of a grid, ends the search;
      // a wrapper round this control alone does not.
      if (table || line) return null;
    }
    return null;
  };
  // Local change: the block a control sits in, so two fields both labelled "Grade"
  // under different headings read differently. The nearest of: an enclosing
  // fieldset's legend, a named group/region/section, or the last heading that
  // precedes the control inside one of its ancestors. It never crosses a dialog.
  const HEADING='h1,h2,h3,h4,h5,h6,[role="heading"]';
  const sections=new Map();
  const sectionOf = e => {
    const start=e.parentElement;
    if (!start) return null;
    if (sections.has(start)) return sections.get(start);
    let found=null;
    for (let node=start, steps=0; node && node!==document.body && steps<12; node=node.parentElement, steps++) {
      if (node.tagName==='FIELDSET') {
        const legend=node.querySelector(':scope > legend');
        if (legend && short(legend)) { found=tidy(flat(legend)); break; }
      }
      const r=node.getAttribute('role');
      if (['group','radiogroup','region'].includes(r) || node.tagName==='SECTION') {
        const label=node.getAttribute('aria-labelledby') ? name(node) : node.getAttribute('aria-label');
        if (label && label.trim()) { found=label.trim().replace(/\s+/g,' ').slice(0,80); break; }
      }
      const before=[...node.querySelectorAll(HEADING)].filter(h=>!h.contains(e) &&
        (h.compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING) && visible(h) && short(h));
      if (before.length) { found=tidy(flat(before[before.length-1])); break; }
      if (node.matches(DIALOG)) break;
    }
    sections.set(start,found);
    return found;
  };
  // Local change: a checkbox or radio styled through its label (the input itself at
  // opacity 0, 1x1 px, clipped or display:none) is offered as that label, which is
  // what a person clicks. Only when the label is visible; the state is the input's.
  const scrollsSideways = e => {
    for (let p=e.parentElement; p && p!==document.body && p!==document.documentElement; p=p.parentElement)
      if (p.scrollWidth>p.clientWidth+2 && /(auto|scroll)/.test(getComputedStyle(p).overflowX)) return true;
    const root=document.scrollingElement||document.documentElement;
    return root.scrollWidth>innerWidth+2 && getComputedStyle(root).overflowX!=='hidden' &&
      getComputedStyle(document.body).overflowX!=='hidden';
  };
  const TOGGLE_MIN=4;
  const hiddenToggle = e => {
    if (e.tagName!=='INPUT' || !['checkbox','radio'].includes(e.type)) return false;
    if (!visible(e)) return true;
    const r=e.getBoundingClientRect();
    return r.width<TOGGLE_MIN || r.height<TOGGLE_MIN;
  };
  const toggleLabel = e => [...(e.labels||[])].find(l=>{
    if (!visible(l)) return false;
    const r=l.getBoundingClientRect();
    return r.width>0 && r.height>0;
  }) || null;
  const weak = (label,value) => !label || GENERIC.has(label.trim().toLowerCase()) ||
    label.trim()===String(value??'').trim();
  // Local change: a type-ahead's suggestions are a list appended to the body, so they
  // carry neither the field's row nor its dialog. Tie each option back to the control
  // that opened it, and say on that control that its list is open.
  const OPTIONISH='[role="option"],[role="menuitem"],[role="menuitemradio"]';
  const OWNER='input:not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit]),'+
    'textarea,select,[role="combobox"],[role="textbox"],[role="searchbox"],[contenteditable="true"]';
  const owners=new Map(), openOwners=new Set();
  const ownerOf = option => {
    for (let node=option; node && node!==document.body; node=node.parentElement) {
      if (!node.id) continue;
      try {
        const named=document.querySelector(
          '[aria-controls~='+JSON.stringify(node.id)+'],[aria-owns~='+JSON.stringify(node.id)+']');
        if (named?.matches(OWNER)) return named;
        if (named) { const inner=named.querySelector(OWNER); if (inner) return inner; }
      } catch { /* an id that is not a valid selector value */ }
    }
    // Then the nearest control the list sits with, then the focused one if its own
    // list is open, then the only open one. Several candidates means no answer:
    // naming the wrong field is worse than naming none.
    for (let node=option.parentElement, steps=0; node && steps<6; node=node.parentElement, steps++) {
      const near=[...node.querySelectorAll(OWNER)].find(c=>visible(c) && !c.closest(OPTIONISH) &&
        c.getAttribute('aria-expanded')==='true');
      if (near) return near;
    }
    const focused=document.activeElement;
    if (focused?.matches?.(OWNER) && focused.getAttribute('aria-expanded')==='true') return focused;
    const open=[...document.querySelectorAll('[aria-expanded="true"]')]
      .map(e=>e.matches(OWNER) ? e : e.querySelector(OWNER)).filter(e=>e && visible(e));
    return open.length===1 ? open[0] : null;
  };
  for (const option of document.querySelectorAll(OPTIONISH)) {
    if (!visible(option)) continue;
    const owner=ownerOf(option);
    if (!owner) continue;
    owners.set(option,owner);
    openOwners.add(owner);
  }
  // Local change: search fields, and the ones among them that open nothing when clicked.
  const searchField=(e,rname)=>e.type==='search' || rname==='searchbox' ||
    !!e.closest('search,[role="search"]');
  const opensSomething=e=>e.hasAttribute('list') || ['aria-haspopup','aria-autocomplete','aria-controls',
    'aria-owns','aria-expanded'].some(a=>{const v=e.getAttribute(a); return v!==null && v!=='false' && v!=='none';});
  const plainSearch=(e,rname)=>rname!=='combobox' && (e.type==='search' || rname==='searchbox') && !opensSomething(e);
  const deepActive=()=>{ let a=document.activeElement; while (a?.shadowRoot?.activeElement) a=a.shadowRoot.activeElement; return a; };
  const actions=[];
  let busyCovers=0;
  for (const e of document.querySelectorAll(selector)) {
    // `hit` is what is pointed at and clicked: the element, or a hidden toggle's label.
    const hit=hiddenToggle(e) ? toggleLabel(e) : e;
    if (!hit) continue;
    if (!safe(e) || !visible(hit) || e.matches(':disabled') || e.closest('[aria-disabled="true"]')) continue;
    const r=hit.getBoundingClientRect(), x=r.x+r.width/2, y=r.y+r.height/2, rname=role(e);
    if (!rname || r.width<=0 || r.height<=0 || y<0 || y>=innerHeight) continue;
    // Local change: a control beyond the right (or left) edge of a horizontally
    // scrolling table is still offered; the executor scrolls it into view first.
    const offscreenX=x<0 || x>=innerWidth;
    if (offscreenX && !scrollsSideways(hit)) continue;
    if (rname==='gridcell' && e.querySelector('button,[role="button"]')) continue;
    const own=name(e), row=rowLabel(e);
    const base={node:identity(hit),role:rname,label:own||rname,
      rect:{x:r.x,y:r.y,w:r.width,h:r.height}};
    if (hit!==e) base.via_label=true;
    if (offscreenX) base.offscreen_x=true;
    if (row) base.row_label=row;
    // A field's row is its label; only a field inside a table row gets a row context.
    const context=rowContext(e, e.matches(OWNER));
    if (context && context!==row && context!==own) base.row_context=context;
    const section=sectionOf(e), landmark=landmarkOf(e);
    if (section) base.section=section;
    if (landmark) base.landmark=landmark;
    if (e.tagName==='INPUT' && TEMPORAL.includes(e.type)) base.input_type=e.type;
    const keys={track_id:e.getAttribute('data-track-id'),dom_id:e.id||null,
      title:e.getAttribute('title'),href:hrefPath(e),ancestor:ancestorTag(e)};
    for (const key in keys) if (keys[key]) base[key]=keys[key];
    if (e.closest(DIALOG)) base.in_dialog=true;
    const owner=owners.get(e);
    if (owner) {
      // A suggestion belongs to the field that opened it, not to the list's own corner of the DOM.
      const ownerRow=rowLabel(owner);
      if (ownerRow) base.row_label=ownerRow;
      if (owner.closest(DIALOG)) base.in_dialog=true;
    }
    if (openOwners.has(e)) base.list_open=true;
    const blocker=offscreenX ? null : coveredAt(hit,x,y);
    if (blocker) {
      base.covered=true;
      base.covered_by=blocker;
      if (BUSYISH.test(blocker)) { base.covered_by_busy=true; busyCovers++; }
    }
    for (const key of ['checked','selected','expanded']) {
      const value=e.getAttribute('aria-'+key);
      if (value!==null) base[key]=value;
    }
    if (['checkbox','radio'].includes(e.type)) base.checked=String(e.checked);
    if (e.tagName==='SELECT') {
      const current=[...e.selectedOptions].map(o=>o.label).join(', ');
      // A <select>'s child text is its option list, never a name for the field.
      const listed=[...e.options].map(o=>o.label).join(' ').trim();
      const shown=row && (weak(own,current) || own.trim()===listed) ? row : base.label;
      for (const o of e.options) if (!o.selected && !o.disabled && !o.closest('optgroup[disabled]'))
        actions.push({...base,kind:'select',value:o.value,
          current_value:current,label:shown+' → '+o.label});
    } else {
      const editable=!e.readOnly && e.getAttribute('aria-readonly')!=='true' &&
        (['textbox','searchbox','spinbutton'].includes(rname) ||
          (rname==='combobox' && ['INPUT','TEXTAREA'].includes(e.tagName)));
      const value='value' in e ? String(e.value) :
        e.isContentEditable || rname==='combobox' ? e.innerText.trim() : '';
      const shown=editable && row && weak(own,value) ? row : base.label;
      actions.push({...base,kind:editable?'fill':'click',value,label:shown});
      // A native date or time picker opens outside the page, where nothing can read it.
      // Local change: nor is there anything to open on a plain search box (no list,
      // no popup, no autocomplete). Offered anyway, its "Open …" click read as a
      // search button, and clicking it did nothing.
      if (editable && !base.input_type && !plainSearch(e, rname))
        actions.push({...base,kind:'click',value,label:'Open '+shown});
      // Local change: a single-line field that holds a value is submitted with Enter.
      // Offered on a search field, or on the field the agent just typed into (the
      // focused one), so a search box with no Search button can run its search.
      if (editable && value.trim() && e.tagName==='INPUT' && !base.input_type &&
          (searchField(e, rname) || e===deepActive()))
        actions.push({...base,kind:'submit',value,label:shown});
    }
  }
  const words=[], walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  const range=document.createRange(); let node,length=0;
  while ((node=walker.nextNode()) && length<6000) {
    const value=node.textContent.trim(), parent=node.parentElement;
    if (!value || !parent || parent.closest('script,style,noscript,template') || !visible(parent)) continue;
    range.selectNodeContents(node); const r=range.getBoundingClientRect();
    if (r.width>0 && r.height>0 && r.bottom>0 && r.top<innerHeight && r.right>0 && r.left<innerWidth) {
      words.push(value); length+=value.length;
    }
  }
  const text=words.join('\n').slice(0,6000), height=document.documentElement.scrollHeight;
  let dialog_title='';
  // Local change: an atlas's `selectors.dialog_title` is tried first, then the
  // built-in heading lookup, then each open dialog's own name (aria-labelledby,
  // aria-label, first heading), topmost first.
  for (const sel of [...(SEL.dialog_title||[]),'[role="dialog"] h1','[role="dialog"] h2','dialog[open] h1',
      'dialog[open] h2','[role="dialog"] [class*="title"]','[aria-modal="true"] h1','[aria-modal="true"] h2']) {
    let hit=null;
    try { hit=[...document.querySelectorAll(sel)].find(e=>visible(e)&&clean(e)); } catch { /* bad selector */ }
    if (hit) { dialog_title=clean(hit).slice(0,200); break; }
  }
  if (!dialog_title) {
    const open=[...document.querySelectorAll(DIALOG)].filter(d=>{
      const r=d.getBoundingClientRect(); return r.width>0 && r.height>0 && visible(d);
    }).reverse();
    for (const d of open) {
      const heading=[...d.querySelectorAll(HEADING)].find(h=>visible(h)&&clean(h));
      const title=(d.getAttribute('aria-labelledby') ? name(d) : '') || d.getAttribute('aria-label') ||
        (heading ? clean(heading) : '');
      if (title && title.trim()) { dialog_title=title.trim().replace(/\s+/g,' ').slice(0,200); break; }
    }
  }
  // A loading mask or spinner is not a settled page; the harness waits it out.
  const busy=busyCovers>0 || [...document.querySelectorAll(BUSY)].some(e=>{
    const r=e.getBoundingClientRect();
    return r.width>0 && r.height>0 && visible(e);
  });
  const headings=[...document.querySelectorAll('h1,h2')]
    .filter(e=>visible(e)&&clean(e)).slice(0,5).map(e=>clean(e).slice(0,200));
  // The largest visible scrolling container: an inner pane scrolls only under the pointer.
  let pane=null, paneArea=0;
  for (const e of document.body.querySelectorAll('*')) {
    if (e.clientHeight<=0 || e.scrollHeight-e.clientHeight<=4) continue;
    if (!/(auto|scroll)/.test(getComputedStyle(e).overflowY) || !visible(e)) continue;
    const r=e.getBoundingClientRect();
    const w=Math.min(r.right,innerWidth)-Math.max(r.left,0);
    const h=Math.min(r.bottom,innerHeight)-Math.max(r.top,0);
    if (w<=0 || h<=0 || w*h<=paneArea) continue;
    paneArea=w*h;
    pane={x:Math.round(Math.max(r.left,0)+w/2),y:Math.round(Math.max(r.top,0)+h/2),
      down:e.scrollTop+e.clientHeight<e.scrollHeight-2,up:e.scrollTop>0};
  }
  const page_key=cache.pageKey(), guards={};
  for (const a of actions) if (!(a.node in guards)) guards[a.node]=cache.guard(cache.nodes.get(a.node));
  // Compare meaning and identity. Geometry is always resolved and hit-tested just before input.
  // `covered` is a hit test of the same kind, so it stays out of the marker: a tooltip or a
  // hover layer passing over a control must not make the whole page look changed.
  const semantics=actions.map(({rect,covered,covered_by,covered_by_busy,...action})=>action);
  const marker=[performance.timeOrigin,location.href,scrollX,scrollY,innerWidth,innerHeight,
    document.title,text,semantics,page_key[6]];
  const omitted_actions=Math.max(0,actions.length-250);
  actions.splice(250);
  actions.forEach((a,i)=>a.id='e'+(i+1));
  const at=pane ? {x:pane.x,y:pane.y} : {};
  if (scrollY+innerHeight<height-2 || pane?.down)
    actions.push({id:'scroll_down',kind:'scroll',label:'Scroll down',delta:560,...at});
  if (scrollY>0 || pane?.up)
    actions.push({id:'scroll_up',kind:'scroll',label:'Scroll up',delta:-560,...at});
  actions.push({id:'wait',kind:'wait',label:'Wait for the page to update'});
  return {url:location.href,title:document.title,w:innerWidth,h:innerHeight,text,
    dialog_title,headings,busy,scroll:{y:scrollY,height,pane},
    actions,marker,page_key,guards,omitted_actions};
})
