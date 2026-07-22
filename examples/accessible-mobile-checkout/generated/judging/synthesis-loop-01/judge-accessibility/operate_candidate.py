from pathlib import Path
from playwright.sync_api import sync_playwright
import json, time

ROOT = Path(r"<skill-repository>")
CANDIDATE = ROOT / ".experiments" / "accessible-mobile-checkout" / "generated" / "synthesis" / "loop-01"
OUT = ROOT / ".experiments" / "accessible-mobile-checkout" / "generated" / "judging" / "synthesis-loop-01" / "judge-accessibility"
SHOTS = OUT / "screenshots"
URL = (CANDIDATE / "index.html").as_uri()
transcript = {"judge_id":"judge-accessibility","model_id":"gpt-5.6-terra","candidate":"candidate-a","iteration":"synthesis-loop-01","viewport":{"width":390,"height":844},"actions":[],"keyboard":[],"controls":[],"landmarks":{},"console":[],"requests":[],"external_requests":[],"checks":{},"screenshots":[]}

def dump():
    (OUT / "navigation-transcript-a.json").write_text(json.dumps(transcript, indent=2), encoding="utf-8")

def ident(page):
    return page.evaluate("""() => { const a=document.activeElement; return {tag:a?.tagName||null,id:a?.id||null,text:(a?.innerText||a?.value||'').trim().slice(0,120),hash:location.hash,scrollY:window.scrollY}; }""")

def state(page):
    return page.evaluate("""() => ({hash:location.hash,scrollY:window.scrollY,status:document.querySelector('[data-hook=status]')?.textContent||'',errorHidden:document.querySelector('[data-hook=error-summary]')?.hidden,confirmationHidden:document.querySelector('[data-hook=confirmation]')?.hidden,active:(document.activeElement?.id || document.activeElement?.getAttribute('data-hook') || document.activeElement?.tagName)})""")

def rec(action, outcome, changed=None, page=None):
    item={"action":action,"outcome":outcome}
    if changed is not None: item["view_or_state_changed"]=changed
    if page is not None: item["observed_state"]=state(page)
    transcript["actions"].append(item)

def shot(page, name):
    path=SHOTS / name
    page.screenshot(path=str(path), full_page=True)
    transcript["screenshots"].append(str(path.relative_to(OUT)).replace('\\','/'))

def control_metadata(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('a, button, input, select, summary')).map((el,i)=>({
        ordinal:i+1, tag:el.tagName.toLowerCase(), id:el.id||null, name:el.getAttribute('name'), hook:el.getAttribute('data-hook'),
        action:el.getAttribute('data-action'), edit_target:el.getAttribute('data-edit-target')||el.getAttribute('data-edit-section'),
        label:(el.labels?.[0]?.innerText || el.innerText || el.getAttribute('aria-label') || el.value || '').trim().replace(/\\s+/g,' ').slice(0,160),
        hidden:!!el.closest('[hidden]'), disabled:!!el.disabled
    }))""")

def fill(page, sel, value):
    page.locator(sel).fill(value)
    rec(f"Fill {sel}", {"value":value if 'card' not in sel else "synthetic payment entered"}, True, page)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width":390,"height":844}, device_scale_factor=1, reduced_motion="no-preference")
    page = context.new_page()
    page.on("console", lambda m: transcript["console"].append({"type":m.type,"text":m.text}))
    page.on("request", lambda r: transcript["requests"].append({"url":r.url,"resource_type":r.resource_type}))
    page.goto(URL, wait_until="load")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="load")
    transcript["controls"] = control_metadata(page)
    transcript["landmarks"] = page.evaluate("""() => ({header:document.querySelectorAll('header').length, main:document.querySelectorAll('main').length, nav:document.querySelectorAll('nav[aria-label="Checkout sections"]').length, aside:document.querySelectorAll('aside[aria-labelledby]').length, footer:document.querySelectorAll('footer').length, form:document.querySelectorAll('form#checkout-form').length, synthetic_note:document.querySelectorAll('[role=note]').length, progressbar:document.querySelectorAll('[role=progressbar]').length, status:document.querySelectorAll('[role=status]').length, alert:document.querySelectorAll('[role=alert]').length, headings:Array.from(document.querySelectorAll('h1,h2,h3')).map(h=>h.textContent.trim())})""")
    shot(page, "01-initial-390x844.png")
    rec("Load local candidate at 390x844", {"landmarks":transcript["landmarks"],"controls_discovered":len(transcript["controls"]),"initial_status":page.locator('[data-hook=status]').inner_text()}, True, page)

    # Keyboard focus traversal and skip-link behavior.
    page.locator('body').focus()
    for i in range(12):
        page.keyboard.press('Tab')
        f=ident(page)
        transcript["keyboard"].append({"action":"Tab","ordinal":i+1,"focus":f})
    page.keyboard.press('Shift+Tab')
    transcript["keyboard"].append({"action":"Shift+Tab","focus":ident(page)})
    page.locator('.skip-link').focus(); page.keyboard.press('Enter'); page.wait_for_timeout(50)
    transcript["keyboard"].append({"action":"Enter on skip link","focus":ident(page),"visible":page.locator('.skip-link').is_visible()})
    rec("Keyboard skip link", {"hash":page.evaluate('location.hash'),"focus_after_enter":ident(page)}, True, page)

    # Every section-navigation link, plus summary close/reopen through keyboard.
    for href in ['#contact','#delivery','#shipping','#payment','#review']:
        before=state(page); page.locator(f'a[href="{href}"]').click(); page.wait_for_timeout(50); after=state(page)
        rec(f"Activate section navigation {href}", {"before":before,"after":after}, before != after, page)
    summary=page.locator('aside summary')
    summary.focus(); page.keyboard.press('Space'); page.wait_for_timeout(50)
    rec("Keyboard Space on order-summary disclosure", {"open":page.locator('aside details').evaluate('(e)=>e.open')}, True, page)
    summary.focus(); page.keyboard.press('Space'); page.wait_for_timeout(50)
    rec("Keyboard Space reopens order-summary disclosure", {"open":page.locator('aside details').evaluate('(e)=>e.open')}, True, page)

    # Invalid submit through the primary button's keyboard activation.
    page.locator('[data-hook=place-order]').focus(); page.keyboard.press('Enter'); page.wait_for_timeout(80)
    invalids=page.locator('[aria-invalid="true"]').count()
    rec("Keyboard Enter on empty Place order", {"error_summary":page.locator('[data-hook=error-summary]').inner_text(),"invalid_field_count":invalids,"focus":ident(page)}, True, page)
    shot(page, "02-error-recovery-390x844.png")
    page.locator('[data-hook=error-summary] a').first.click(); page.wait_for_timeout(50)
    rec("Activate first grouped error-summary link", {"focus":ident(page),"target":"contact-name"}, True, page)

    # Correct safe values, save, and reload to establish interruption behavior.
    safe_values={
        '#contact-name':'Alex Morgan','#contact-email':'alex.morgan@example.invalid','#contact-phone':'+61 400 000 000',
        '#address-line1':'42 Fiction Lane','#address-city':'Sampleton','#address-state':'NSW','#address-postcode':'2000','#address-country':'Australia'
    }
    for sel, value in safe_values.items(): fill(page, sel, value)
    page.locator('#shipping-standard').focus(); page.keyboard.press('ArrowDown'); page.wait_for_timeout(40)
    transcript["keyboard"].append({"action":"ArrowDown on shipping radio","focus":ident(page),"checked":page.locator('#shipping-express').is_checked(),"total":page.locator('[data-hook=total]').inner_text()})
    rec("Keyboard ArrowDown selects Express shipping", {"express_checked":page.locator('#shipping-express').is_checked(),"total":page.locator('[data-hook=total]').inner_text()}, True, page)
    page.locator('#shipping-express').focus(); page.keyboard.press('ArrowUp'); page.wait_for_timeout(40)
    transcript["keyboard"].append({"action":"ArrowUp on shipping radio","focus":ident(page),"checked_standard":page.locator('#shipping-standard').is_checked(),"total":page.locator('[data-hook=total]').inner_text()})
    rec("Keyboard ArrowUp returns Standard shipping", {"standard_checked":page.locator('#shipping-standard').is_checked(),"total":page.locator('[data-hook=total]').inner_text()}, True, page)
    # Make an invalid payment entry then submit: completed safe values must survive errors.
    fill(page, '#card-number', '4111')
    page.locator('[data-hook=place-order]').focus(); page.keyboard.press('Enter'); page.wait_for_timeout(60)
    preserved=page.locator('#contact-email').input_value()
    rec("Submit with invalid payment after valid contact/delivery", {"preserved_contact_email":preserved,"card_error":page.locator('#card-number-error').inner_text(),"summary_visible":page.locator('[data-hook=error-summary]').is_visible()}, True, page)
    # Clear payment content before persistence checks.
    for sel in ['#card-number','#card-expiry','#card-security','#card-name']: page.locator(sel).fill('')
    page.locator('[data-action=save-now]').focus(); page.keyboard.press('Space'); page.wait_for_timeout(50)
    saved=page.evaluate("JSON.parse(localStorage.getItem('northstar-synthesis-checkout'))")
    rec("Keyboard Space saves safe progress", {"status":page.locator('[data-hook=status]').inner_text(),"saved_keys":sorted(saved.keys()),"stored_field_keys":sorted(saved.get('fields',{}).keys()),"contains_payment_secret":any('card' in json.dumps(saved).lower() for _ in [0])}, True, page)
    page.reload(wait_until='load'); page.wait_for_timeout(60)
    restored={sel:page.locator(sel).input_value() for sel in safe_values}
    payment_after_reload={sel:page.locator(sel).input_value() for sel in ['#card-number','#card-expiry','#card-security','#card-name']}
    rec("Reload restores safe fields only", {"restored_safe_values":restored,"payment_values_after_reload":payment_after_reload,"status":page.locator('[data-hook=status]').inner_text()}, True, page)

    # Confirmed clear operation: Escape, Cancel, then explicit confirmation and reload.
    page.locator('[data-action=clear-progress]').focus(); page.keyboard.press('Enter'); page.wait_for_timeout(40)
    rec("Keyboard Enter opens clear-progress confirmation", {"dialog_visible":page.locator('#clear-confirm').is_visible(),"focus":ident(page),"aria_expanded":page.locator('[data-action=clear-progress]').get_attribute('aria-expanded')}, True, page)
    shot(page, "03-save-clear-confirmation-390x844.png")
    page.keyboard.press('Escape'); page.wait_for_timeout(40)
    rec("Escape dismisses clear-progress confirmation", {"dialog_visible":page.locator('#clear-confirm').is_visible(),"status":page.locator('[data-hook=status]').inner_text(),"stored":page.evaluate("localStorage.getItem('northstar-synthesis-checkout') !== null")}, True, page)
    page.locator('[data-action=clear-progress]').click(); page.wait_for_timeout(20); page.locator('[data-action=cancel-clear]').click(); page.wait_for_timeout(30)
    rec("Activate Cancel clear-progress control", {"dialog_visible":page.locator('#clear-confirm').is_visible(),"stored":page.evaluate("localStorage.getItem('northstar-synthesis-checkout') !== null")}, True, page)
    page.locator('[data-action=clear-progress]').click(); page.wait_for_timeout(20); page.locator('[data-action=confirm-clear]').click(); page.wait_for_timeout(100)
    rec("Activate Yes, clear saved progress", {"stored_after_clear":page.evaluate("localStorage.getItem('northstar-synthesis-checkout')"),"safe_name_after_reload":page.locator('#contact-name').input_value()}, True, page)

    # Build the complete valid checkout again, exercising each remaining form control.
    for sel, value in safe_values.items(): fill(page, sel, value)
    page.locator('#shipping-express').click(); page.wait_for_timeout(30)
    rec("Pointer activation of Express shipping control", {"express_checked":page.locator('#shipping-express').is_checked(),"total":page.locator('[data-hook=total]').inner_text()}, True, page)
    for sel, value in {'#card-number':'4111 1111 1111 1111','#card-expiry':'12/34','#card-security':'123','#card-name':'Alex Morgan'}.items(): fill(page, sel, value)
    page.locator('#review-confirmation').focus(); page.keyboard.press('Space'); page.wait_for_timeout(30)
    transcript["keyboard"].append({"action":"Space on review confirmation","focus":ident(page),"checked":page.locator('#review-confirmation').is_checked()})
    rec("Keyboard Space confirms review", {"review_checked":page.locator('#review-confirmation').is_checked(),"progress":page.locator('[data-hook=progress]').get_attribute('aria-valuetext')}, True, page)

    # Compact completed sections and every direct edit control.
    page.locator('#compact-completed').focus(); page.keyboard.press('Space'); page.wait_for_timeout(80)
    compacted=page.evaluate("""() => ['contact','delivery','shipping','payment'].map(id=>({id,compacted:document.querySelector('#'+id).dataset.compacted,hidden:document.querySelector('#'+id+' [data-section-body]').hidden,focusableHidden:Array.from(document.querySelectorAll('#'+id+' [data-section-body] a,#'+id+' [data-section-body] button,#'+id+' [data-section-body] input,#'+id+' [data-section-body] select')).filter(e=>!e.closest('[hidden]')).length}))""")
    rec("Keyboard Space enables compact completed sections", {"compacted_sections":compacted,"status":page.locator('[data-hook=status]').inner_text()}, True, page)
    shot(page, "04-compact-edit-390x844.png")
    for target in ['contact','delivery','shipping','payment']:
        page.locator(f'[data-edit-section="{target}"]').click(); page.wait_for_timeout(30)
        rec(f"Activate compact-section Edit {target}", {"focus":ident(page),"compacted":page.locator(f'#{target}').get_attribute('data-compacted')}, True, page)
    for target in ['contact','delivery','shipping','payment']:
        page.locator(f'[data-edit-target="{target}"]').click(); page.wait_for_timeout(30)
        rec(f"Activate review Edit {target}", {"focus":ident(page)}, True, page)
    # Ensure payment remains complete and review checkbox state survives Edit controls.
    rec("Verify review confirmation survives edits", {"review_checked":page.locator('#review-confirmation').is_checked()}, False, page)

    # Local busy status and single confirmation, completed via primary keyboard activation.
    page.locator('[data-hook=place-order]').focus(); page.keyboard.press('Enter'); page.wait_for_timeout(30)
    rec("Keyboard Enter begins local placement", {"status_during_delay":page.locator('[data-hook=status]').inner_text(),"busy":page.locator('[data-hook=place-order]').get_attribute('aria-busy')}, True, page)
    page.wait_for_timeout(240)
    confirmation_count=page.locator('[data-hook=confirmation-id]').count()
    rec("Observe local confirmation", {"confirmation_count":confirmation_count,"confirmation_id":page.locator('[data-hook=confirmation-id]').inner_text(),"focus":ident(page),"status":page.locator('[data-hook=status]').inner_text()}, True, page)
    shot(page, "05-confirmation-390x844.png")
    # A second native submit attempts the duplicate path without re-enabling the disabled button.
    page.locator('#checkout-form').evaluate("form => form.requestSubmit()")
    page.wait_for_timeout(20)
    rec("Attempt duplicate native form submission after confirmation", {"confirmation_count":page.locator('[data-hook=confirmation-id]').count(),"status":page.locator('[data-hook=status]').inner_text(),"place_order_disabled":page.locator('[data-hook=place-order]').is_disabled()}, True, page)

    # Small-screen touch/overflow and reduce-motion checks in isolated contexts.
    transcript['checks']['mobile_390'] = page.evaluate("""() => { const all=Array.from(document.querySelectorAll('a,button,input,select,summary')); const rects=all.filter(e=>!e.closest('[hidden]')).map(e=>{const r=e.getBoundingClientRect();return {label:(e.innerText||e.value||e.id||e.tagName).trim().slice(0,80),width:r.width,height:r.height};}); return {document_scroll_width:document.documentElement.scrollWidth,viewport_width:window.innerWidth,overflow:document.documentElement.scrollWidth>window.innerWidth,minimum_target_height:Math.min(...rects.map(r=>r.height)),minimum_target_width:Math.min(...rects.map(r=>r.width)),targets:rects}; }""")
    rm_context=browser.new_context(viewport={"width":390,"height":844}, reduced_motion="reduce")
    rm_page=rm_context.new_page(); rm_page.goto(URL, wait_until='load')
    transcript['checks']['reduced_motion'] = rm_page.evaluate("""() => {const s=getComputedStyle(document.querySelector('.task-section')); return {media_matches:matchMedia('(prefers-reduced-motion: reduce)').matches,transition_duration:s.transitionDuration,animation_duration:s.animationDuration,scroll_behavior:getComputedStyle(document.documentElement).scrollBehavior};}""")
    rm_context.close()
    transcript['external_requests']=[r for r in transcript['requests'] if not r['url'].startswith('file:')]
    transcript['checks']['console_error_count']=sum(1 for c in transcript['console'] if c['type'] in ('error','warning'))
    transcript['checks']['one_confirmation']=page.locator('[data-hook=confirmation-id]').count()==1
    dump()
    context.close(); browser.close()
print('Wrote', OUT / 'navigation-transcript-a.json')
