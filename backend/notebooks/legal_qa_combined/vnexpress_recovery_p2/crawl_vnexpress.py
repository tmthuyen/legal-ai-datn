"""VnExpress civil law Q&A: collect infinite-scroll URLs then visit individual articles.
Run: python crawl_vnexpress.py --out output/vnexpress --max-scrolls 150
"""
import argparse,csv,hashlib,json,re,time,random
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

START='https://vnexpress.net/phap-luat/tu-van/dan-su'
SELECTOR='#list-news article.item-news h4.title-news a[href]'
LEGAL_RE=re.compile(r'(?:(?:các?\s+)?(?:khoản\s+[\d]+(?:\s*[,và]+\s*khoản\s*\d+)*\s*)?(?:điểm\s+[a-zđ]\s+)?Điều\s+\d+(?:\s*[,và]+\s*Điều\s*\d+)*)\s+(?:của\s+)?(?:Bộ luật|Luật|Nghị định|Nghị quyết|Thông tư)[^\n.;:]{0,125}',re.IGNORECASE)
ARTICLE_RE=re.compile(r'-(\d{6,9})\.html$')

def canonical(url):
    p=urlsplit(url)
    return urlunsplit((p.scheme or 'https',p.netloc,p.path,'',''))

def clean(s):return re.sub(r'\s+',' ',s or '').strip()

def lines_of(node):
    if not node:return []
    return [clean(p.get_text(' ',strip=True)) for p in node.select(':scope > p') if clean(p.get_text(' ',strip=True))]

def parse_listing(html):
    soup=BeautifulSoup(html,'html.parser')
    items=[]
    for article in soup.select('#list-news article.item-news'):
        a=article.select_one('h4.title-news a[href]')
        if not a:continue
        url=canonical(a['href'])
        if not ARTICLE_RE.search(url):continue
        lead=article.select_one('p.description')
        items.append({'url':url,'title':clean(a.get_text(' ',strip=True)),
                      'description':clean(lead.get_text(' ',strip=True)) if lead else '',
                      'source':'VnExpress','category':'Dân sự',
                      'source_category_url':START})
    container=soup.select_one('#list-news')
    return items, container.get('data-next-page') if container else None

def parse_article(html,url):
    soup=BeautifulSoup(html,'html.parser')
    root=soup.select_one('article.fck_detail') or soup.select_one('.fck_detail')
    if not root: raise ValueError('Không tìm thấy article.fck_detail')
    title=root.select_one('h1.title-detail') or soup.select_one('h1.title-detail')
    desc=root.select_one('p.description')
    # Only direct article paragraphs, never poll widgets, comments, advertisements.
    paragraphs=lines_of(root)
    marker=next((i for i,x in enumerate(paragraphs) if re.search(r'^Luật sư tư vấn\s*:',x,re.I)),None)
    if marker is None:
        raise ValueError('Không thấy nhãn Luật sư tư vấn:; lưu trạng thái chờ kiểm tra')
    question_parts=([clean(desc.get_text(' ',strip=True))] if desc else [])+paragraphs[:marker]
    # Avoid duplicate description when site repeats it as a direct paragraph.
    question_parts=list(dict.fromkeys(x for x in question_parts if x))
    answer_parts=paragraphs[marker+1:]
    # Remove last paragraph if lawyer attribution; retain raw text in metadata.
    lawyer=None
    if answer_parts and re.search(r'^(Luật sư|LS\.)\s+',answer_parts[-1],re.I):
        lawyer=answer_parts.pop()
    elif answer_parts and 'Luật sư ' in answer_parts[-1] and len(answer_parts[-1]) < 160:
        lawyer=answer_parts.pop()
    question='\n'.join(question_parts)
    answer='\n'.join(answer_parts)
    citations=[]
    # Split multiple references linked by 'và', preserving the original answer.
    citation_search_text=re.sub(r'\s+và\s+(?=(?:khoản|Điều|điểm)\s+\d+)', '; ', answer, flags=re.I)
    for match in LEGAL_RE.finditer(citation_search_text):
        raw=clean(match.group())
        if not raw:continue
        citations.append({'raw_text':raw,'source_field':'answer','extraction_method':'regex',
           'verified':False,'verification_status':'not_verified','char_start':match.start(),'char_end':match.end()})
    # Deduplicate cited text preserving order
    citations=list({x['raw_text'].lower():x for x in citations}.values())
    pub=soup.select_one('meta[property="article:published_time"]') or soup.select_one('meta[name="pubdate"]')
    date=pub.get('content') if pub else None
    if not date:
        t=soup.select_one('span.date') or soup.select_one('.header-content .date')
        date=clean(t.get_text(' ',strip=True)) if t else None
    url=canonical(url)
    return {'id':'vne_'+(ARTICLE_RE.search(url).group(1) if ARTICLE_RE.search(url) else hashlib.sha256(url.encode()).hexdigest()[:16]),
       'url':url,'title':clean(title.get_text(' ',strip=True)) if title else None,
       'source':'VnExpress','category':'Dân sự','source_category_url':START,'published_at_raw':date,
       'question':question,'answer':answer,'content':question+'\n\n'+answer,
       'citation':citations,'relevant_law':[], 'lawyer':lawyer,
       'citation_verified':False,'extraction_status':'full_qa' if question and answer else 'incomplete',
       'civil_code_2015_scope':'not_reviewed',
       'content_sha256':hashlib.sha256((question+'\n\n'+answer).encode()).hexdigest(),
       'collected_at_utc':datetime.now(timezone.utc).isoformat()}

def write_jsonl(path,rows):
    with open(path,'w',encoding='utf8') as f:
        for x in rows:f.write(json.dumps(x,ensure_ascii=False)+'\n')

def write_csv(path,rows,columns):
    with open(path,'w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        for row in rows:w.writerow({k:(json.dumps(row[k],ensure_ascii=False) if isinstance(row.get(k),(dict,list)) else row.get(k,'')) for k in columns})

def crawl(out,max_scrolls,delay,headless):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    urls={};errors=[];articles=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=headless)
        page=browser.new_page(viewport={'width':1440,'height':900},locale='vi-VN')
        page.goto(START,wait_until='domcontentloaded',timeout=60000)
        page.locator('#list-news article.item-news').first.wait_for(timeout=30000)
        stagnation=0
        for i in range(max_scrolls+1):
            batch,next_page=parse_listing(page.content())
            before=len(urls)
            for item in batch:urls[item['url']]=item
            print(f'[LIST] step={i} total={len(urls)} next_page={next_page}',flush=True)
            write_jsonl(out/'article_urls.jsonl',list(urls.values()))
            write_csv(out/'article_urls.csv',list(urls.values()),['url','title','description','source','category','source_category_url'])
            if i==max_scrolls:break
            count=page.locator(SELECTOR).count()
            page.evaluate('window.scrollTo(0,document.body.scrollHeight)')
            try:
                page.wait_for_function('n => document.querySelectorAll("#list-news article.item-news h4.title-news a[href]").length > n',arg=count,timeout=12000)
            except Exception:
                # Some pages have an explicit 'Xem thêm' control rather than pure observer.
                more=page.locator('a:has-text("Xem thêm"), button:has-text("Xem thêm")')
                if more.count():
                    try:more.last.click(timeout=1500)
                    except Exception:pass
                page.wait_for_timeout(1600)
            count_after=page.locator(SELECTOR).count()
            stagnation=stagnation+1 if count_after==count and len(urls)==before else 0
            if stagnation>=3:
                print('[STOP] Three consecutive scroll attempts found no new article.',flush=True)
                break
            time.sleep(delay+random.uniform(0,.35))
        detail=browser.new_page(locale='vi-VN')
        for j,meta in enumerate(urls.values(),1):
            try:
                detail.goto(meta['url'],wait_until='domcontentloaded',timeout=45000)
                detail.locator('article.fck_detail').wait_for(timeout=10000)
                row=parse_article(detail.content(),meta['url'])
                row['listing_description']=meta['description']
                articles.append(row)
                print(f'[DETAIL] {j}/{len(urls)} {row["extraction_status"]} {len(row["citation"])} citations',flush=True)
            except Exception as e:
                errors.append({'url':meta['url'],'error':str(e)})
                print(f'[ERROR] {j}/{len(urls)} {meta["url"]}: {e}',flush=True)
            write_jsonl(out/'legal_qa.jsonl',articles)
            write_jsonl(out/'crawl_errors.jsonl',errors)
            time.sleep(delay+random.uniform(0,.35))
        browser.close()
    write_csv(out/'legal_qa.csv',articles,['id','url','title','source','category','published_at_raw','question','answer','content','citation','relevant_law','lawyer','extraction_status','civil_code_2015_scope','content_sha256'])
    print(f'Done: {len(urls)} URLs, {len(articles)} articles, {len(errors)} failures')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',default='output/vnexpress')
    ap.add_argument('--max-scrolls',type=int,default=150)
    ap.add_argument('--delay',type=float,default=2.0)
    ap.add_argument('--headed',action='store_true')
    args=ap.parse_args()
    crawl(args.out,args.max_scrolls,args.delay,not args.headed)
