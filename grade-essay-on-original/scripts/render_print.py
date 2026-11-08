#!/usr/bin/env python3
"""Render already-reviewed essay annotations. Does not OCR, grade or call a provider."""
import argparse, hashlib, json, re
from pathlib import Path
import fitz

FONT = fitz.Font('cjk')
RED, GRAY, INK = (.8,.12,.14), (.38,.42,.46), (.12,.17,.22)
W,H = fitz.paper_size('a4-l')
TOP,BOTTOM = 85,552

def open_source(path):
    doc=fitz.open(path)
    if not doc.is_pdf:
        pdf=fitz.open('pdf',doc.convert_to_pdf());doc.close();return pdf
    return doc

def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def wrap(s,width,size=10.4):
    result=[];line='';tokens=[]
    closing='，。！？；：、）》】”’…,.!?;:)]}'
    for tok in re.findall(r"[A-Za-z0-9]+(?:[’'/-][A-Za-z0-9]+)*|\n|[ \t]+|.",s):
        if tok and tok[0] in closing and tokens and not tokens[-1].isspace():tokens[-1]+=tok
        else:tokens.append(tok)
    for tok in tokens:
        if tok=='\n':result.append(line);line='';continue
        if FONT.text_length(line+tok,fontsize=size)<=width:line+=tok;continue
        if line.strip():result.append(line.rstrip());line=''
        if FONT.text_length(tok,fontsize=size)<=width:line=tok.lstrip();continue
        for c in tok:
            if FONT.text_length(line+c,fontsize=size)>width:
                if c in closing and len(line)>1:
                    result.append(line[:-1]);line=line[-1]
                else:result.append(line);line=''
            line+=c
    if line:result.append(line.rstrip())
    return result

def note_lines(n,width):
    return [l for key,prefix in [('old','原：'),('new','→ '),('reason','理由：')]
            for l in wrap(prefix+n[key],width)]

def height(n,width):return 40+13.6*len(note_lines(n,width))

def pack(notes,width,available):
    groups=[];group=[];used=0
    for n in notes:
        size=height(n,width)
        if size>available:raise ValueError('单条批注超过可用区域：请缩短解释或调整分区，不能缩小字体')
        if group and used+size>available:groups.append(group);group=[];used=0
        group.append(n);used+=size
    if group:groups.append(group)
    return groups or [[]]

def txt(page,x,y,s,size=10.4,color=INK):
    page.insert_text((x,y),s,fontname='CN',fontsize=size,color=color)

def header(page,title,label,provider):
    page.insert_font(fontname='CN',fontbuffer=FONT.buffer)
    if FONT.text_length(title,fontsize=16)>W-45:raise ValueError('标题过长，请缩短')
    txt(page,20,28,title,16);txt(page,20,48,label,10.4)
    for x,dash,color,label in [(20,None,RED,'纠错建议'),(171,'[3 3] 0',RED,'可选润色'),(322,None,GRAY,'待核对')]:
        page.draw_rect(fitz.Rect(x,58,x+25,68),color=color,width=1,dashes=dash)
        txt(page,x+32,67,label,9.5,color)
    page.draw_line((20,75),(W-20,75),color=(.82,.85,.88),width=.6)
    footer=f'{provider}；建议需教师核对。打印：A4横向／实际大小。'
    if FONT.text_length(footer,fontsize=8.6)>W-40:raise ValueError('provider_status 过长，请保留简短实际调用状态')
    txt(page,20,H-24,footer,8.6,GRAY)

def draw_note(page,n,x,y,width):
    color=GRAY if n['type']=='check' else RED
    kind={'error':'纠错建议','optional':'可选润色','check':'待核对'}[n['type']]
    txt(page,x,y+11,f'{n["id"]:02}  {kind}',10.8,color)
    yy=y+27
    for line in note_lines(n,width):txt(page,x,yy,line);yy+=13.6
    page.draw_line((x,yy+1),(x+width,yy+1),color=(.88,.9,.92),width=.4)
    return yy+13

def marks(page,notes,clip,target):
    scale=target.width/clip.width
    for n in notes:
        color=GRAY if n['type']=='check' else RED
        dash='[3 2] 0' if n['type']=='optional' else None
        for box in n['boxes']:
            b=fitz.Rect(box)
            q=fitz.Rect(target.x0+(b.x0-clip.x0)*scale,target.y0+(b.y0-clip.y0)*scale,
                        target.x0+(b.x1-clip.x0)*scale,target.y0+(b.y1-clip.y0)*scale)
            page.draw_rect(q,color=color,width=.85 if n['type']=='check' else 1.1,dashes=dash)
            # No opaque label backgrounds: preserve every student mark.
            txt(page,q.x0,q.y1+8.5,f'{n["id"]:02}',6.8,color)

def prepare(paths,out):
    out.mkdir(parents=True,exist_ok=True);sources=[]
    for idx,path in enumerate(paths,1):
        path=Path(path).resolve();doc=open_source(path);sid=f's{idx}'
        entry={'id':sid,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pages':[]}
        for i,p in enumerate(doc,1):
            png=out/f'{sid}_page_{i:03}.png'
            p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(png)
            entry['pages'].append({'page':i,'width':p.rect.width,'height':p.rect.height,'preview':str(png),'preview_scale':1.5})
        sources.append(entry);doc.close()
    write_json(out/'sources.json',{'sources':sources})
    print(json.dumps({'sources':len(sources),'pages':sum(len(s['pages']) for s in sources),'manifest':str(out/'sources.json')},ensure_ascii=False))

def render(planpath,outdir):
    plan=json.loads(Path(planpath).read_text(encoding='utf-8'));outdir.mkdir(parents=True,exist_ok=True)
    dest=outdir/'print.pdf'
    if dest.exists():raise ValueError('目标PDF已存在：请使用新的版本目录，保留历史版本')
    sources={};source_records=[]
    for s in plan['sources']:
        if s['id'] in sources:raise ValueError('源文件ID重复')
        path=Path(s['path']).resolve();sources[s['id']]=open_source(path)
        source_records.append({'id':s['id'],'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    output=fitz.open();mapping=[];toc=[]
    for e in plan['essays']:
        source=sources[e['source']];pn=e['page'];original=source[pn-1]
        if pn<1:raise ValueError('页码必须从1开始')
        crop=fitz.Rect(e.get('crop',original.rect))
        if crop.is_empty or not original.rect.contains(crop):raise ValueError('裁切超出原页')
        notes=e.get('notes',[])
        for i,n in enumerate(notes,1):
            n['id']=i
            if n['type'] not in {'error','optional','check'}:raise ValueError('批注类别错误')
            if any(not isinstance(n.get(k),str) or not n[k].strip() for k in ['old','new','reason']):raise ValueError('批注文字缺失')
            if not n.get('boxes'):raise ValueError('批注缺少原图位置')
            for box in n['boxes']:
                r=fitz.Rect(box)
                if r.is_empty or not crop.contains(r):raise ValueError(f'批注 {i} 越界')
        regions=[fitz.Rect(r) for r in e.get('regions',[list(crop)])]
        assignments=[[] for _ in regions]
        for n in notes:
            b=fitz.Rect(n['boxes'][0]);center=fitz.Point((b.x0+b.x1)/2,(b.y0+b.y1)/2)
            candidates=[i for i,r in enumerate(regions) if r.contains(center)]
            if not candidates:raise ValueError('存在未分配到原图分区的批注')
            assignments[candidates[0]].append(n)
        toc.append([1,e.get('label',f'原第{pn}页'),len(output)+1])
        for ri,(region,ns) in enumerate(zip(regions,assignments),1):
            if region.is_empty or not crop.contains(region):raise ValueError('原图分区越界')
            clip=fitz.Rect(region)
            for n in ns:
                for box in n['boxes']:clip.include_rect(fitz.Rect(box))
            layout=e.get('layout','left-right')
            if layout not in {'left-right','wide'}:raise ValueError('未知版式')
            if layout=='wide':
                scale=min(780/clip.width,280/clip.height);imageheight=clip.height*scale
                ntop=TOP+imageheight+19;columns=pack(ns,388,BOTTOM-ntop)
                chunks=[columns[i:i+2] for i in range(0,len(columns),2)]
            else:
                scale=min(518/clip.width,(BOTTOM-TOP)/clip.height);ntop=TOP
                chunks=[[c] for c in pack(ns,238,BOTTOM-TOP)]
            for ci,columns in enumerate(chunks,1):
                p=output.new_page(width=W,height=H)
                label=f'{e.get("label",f"原第{pn}页")} | 分区{ri}/{len(regions)} | 批注页{ci}/{len(chunks)}'
                header(p,plan.get('title','英语作文 · 原图批改建议'),label,plan.get('provider_status','直接原图审阅；外部调用0次'))
                target=fitz.Rect(22,TOP,22+clip.width*scale,TOP+clip.height*scale)
                p.show_pdf_page(target,source,pn-1,clip=clip)
                chunk=[n for col in columns for n in col];marks(p,chunk,clip,target)
                for col,colnotes in enumerate(columns):
                    yy=ntop
                    for n in colnotes:yy=draw_note(p,n,22+col*410 if layout=='wide' else 584,yy,388 if layout=='wide' else 238)
                    if yy>BOTTOM+.1:raise ValueError('批注排版溢出')
                if not chunk:txt(p,584,TOP+20,'本分区未标出建议项。',10.4,GRAY)
                mapping.append({'output_page':len(output),'source':e['source'],'source_page':pn,'crop':list(clip),'notes':[n['id'] for n in chunk]})
        ids=[i for m in mapping if m['source']==e['source'] and m['source_page']==pn for i in m['notes']]
        if ids!=list(range(1,len(notes)+1)):raise ValueError('批注顺序或覆盖异常；同一源页应只配置一次')
    output.set_toc(toc);output.subset_fonts();output.save(dest,garbage=4,deflate=True)
    for i,p in enumerate(output,1):p.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(outdir/f'page_{i:03}.png')
    write_json(outdir/'plan_used.json',plan);write_json(outdir/'layout.json',{'sources':source_records,'pages':mapping})
    print(json.dumps({'pdf':str(dest),'pages':len(output),'notes':sum(len(e.get('notes',[])) for e in plan['essays']),'next':'逐页查看输出PNG并核对字迹、位置、编号、裁切和分页；再保存交付'},ensure_ascii=False))
    output.close()
    for doc in sources.values():doc.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);subs=parser.add_subparsers(dest='command',required=True)
    p=subs.add_parser('prepare');p.add_argument('paths',nargs='+');p.add_argument('--out-dir',type=Path,required=True)
    p=subs.add_parser('render');p.add_argument('plan');p.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='prepare':prepare(args.paths,args.out_dir)
    else:render(args.plan,args.out_dir)
