"""Publication figures: one measured geometry for editable TikZ and SVG.

All coordinates are physical points at the final ACL width. Values and saved
intervals come from the verified artifacts; this module does not fit or test data.
Color has a stable role: orange = inaccessible/full-context influence,
blue = accessible content, green = compiled character view. Shapes and numbers
make the comparisons readable in monochrome as well.
"""
import html

INK = '#222222'
MUTED = '#646B73'
GRID = '#DDE1E5'
PALE = '#F4F6F8'
ORANGE = '#B04A00'
BLUE = '#0072B2'
GREEN = '#007A5E'
BOUNDS = ('Hear', 'Understand', 'See', 'Receive')


def tint(color, value):
    """Linear, labeled 0--100 scale, never normalized separately per row."""
    rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    t = max(0, min(1, value / 100))
    return '#' + ''.join(f'{round(250 * (1-t) + c*t):02x}' for c in rgb)


def cell_text_color(color):
    rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
    linear = [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    luminance = sum(v*w for v,w in zip(linear,(.2126,.7152,.0722)))
    # Select the stronger black/white contrast at the actual saved cell value.
    return '#000000' if luminance>=.179 else '#FFFFFF'


def tex_color(color):
    r, g, b = (int(color[i:i+2], 16) for i in (1, 3, 5))
    return '{rgb,255:red,%d;green,%d;blue,%d}' % (r, g, b)


class Canvas:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.tikz = [r'\begin{tikzpicture}[x=1pt,y=-1pt]',
                     f'\\path[use as bounding box] (0,0) rectangle ({width},{height});']
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width*3}" height="{height*3}" viewBox="0 0 {width} {height}">',
                    f'<rect width="{width}" height="{height}" fill="white"/>',
                    '<g font-family="Times New Roman, Times, serif">']

    def text(self, x, y, text, size=9, color=INK, bold=False, anchor='start', tex=None):
        ta = {'start': 'west', 'middle': 'center', 'end': 'east'}[anchor]
        weight = r'\bfseries' if bold else ''
        # Center anchors are shared; SVG central baseline is nudged consistently.
        content = tex if tex is not None else text.replace('%', r'\%').replace('&', r'\&')
        self.tikz.append(f'\\node[anchor={ta},inner sep=0pt,text={tex_color(color)},font=\\fontsize{{{size}}}{{{size+1}}}\\selectfont{weight}] at ({x:.4f},{y:.4f}) {{{content}}};')
        self.svg.append(f'<text x="{x:.4f}" y="{y+size*.32:.4f}" font-size="{size}" font-weight="{"bold" if bold else "normal"}" fill="{color}" text-anchor="{anchor}">{html.escape(text)}</text>')

    def line(self, x1, y1, x2, y2, color=GRID, width=.5, dashed=False):
        dash = ',dash pattern=on 2pt off 2pt' if dashed else ''
        self.tikz.append(f'\\draw[draw={tex_color(color)},line width={width}pt{dash}] ({x1:.4f},{y1:.4f})--({x2:.4f},{y2:.4f});')
        self.svg.append(f'<line x1="{x1:.4f}" y1="{y1:.4f}" x2="{x2:.4f}" y2="{y2:.4f}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="2 2"' if dashed else '')+'/>')

    def rect(self, x, y, w, h, fill):
        self.tikz.append(f'\\fill[fill={tex_color(fill)}] ({x:.4f},{y:.4f}) rectangle ({x+w:.4f},{y+h:.4f});')
        self.svg.append(f'<rect x="{x:.4f}" y="{y:.4f}" width="{w:.4f}" height="{h:.4f}" fill="{fill}"/>')

    def polygon(self, points, fill):
        self.tikz.append(f'\\fill[fill={tex_color(fill)}] '+'--'.join(f'({x:.4f},{y:.4f})' for x,y in points)+'--cycle;')
        self.svg.append(f'<polygon points="'+ ' '.join(f'{x:.4f},{y:.4f}' for x,y in points)+f'" fill="{fill}"/>')

    def marker(self, x, y, color, shape='circle', hollow=False, radius=1.8):
        if shape == 'triangle':
            self.polygon([(x, y-radius*1.2), (x-radius, y+radius*.7), (x+radius, y+radius*.7)], color)
        elif shape == 'square':
            self.rect(x-radius, y-radius, 2*radius, 2*radius, color)
        else:
            fill = '#FFFFFF' if hollow else color
            self.tikz.append(f'\\draw[draw={tex_color(color)},fill={tex_color(fill)},line width=.7pt] ({x:.4f},{y:.4f}) circle[radius={radius}pt];')
            self.svg.append(f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{radius}" fill="{fill}" stroke="{color}" stroke-width=".7"/>')

    def whisker(self, x1, x2, y, color, width=.85, caps=1.6):
        self.line(x1, y, x2, y, color, width)
        self.line(x1, y-caps, x1, y+caps, color, .65)
        self.line(x2, y-caps, x2, y+caps, color, .65)

    def exports(self):
        return '\n'.join(self.tikz+[r'\end{tikzpicture}']), '\n'.join(self.svg+['</g></svg>'])


def discovery_profiles(baseline, accessible, models, labels, core):
    """88 channel cells plus 22 equal-channel mean markers; no uncertainty inferred."""
    c = Canvas(455, 195)
    leak = {(r['model'], r['boundary']): 100*r['estimate'] for r in baseline}
    allowed = {(r['model'], r['boundary']): 100*r['estimate'] for r in accessible}
    c.text(0, 9, 'Model', bold=True)
    c.text(96, 9, '(a) Inaccessible net use (pp)', bold=True)
    c.text(249, 9, '(b) Accessible target use (%)', bold=True)
    c.text(405, 9, '(c) Mean', bold=True, size=8.5)
    for j,b in enumerate(BOUNDS):
        for x0 in (96,249):
            c.text(x0+18+36*j, 25, b, anchor='middle', size=8.3)
    for value in (0,50,100):
        x=405+value*.47
        c.line(x, 33, x, 165, GRID, .4)
        c.text(x, 25, str(value), size=8, anchor='end' if value==100 else 'middle', color=MUTED)
    for i,m in enumerate(models):
        y=34+12*i
        if i%2 == 0:c.rect(0,y,455,12,PALE)
        label=labels[m]
        c.text(88,y+6,label,anchor='end',size=9)
        if m in core:c.marker(92,y+6,INK,radius=1.1)
        for x0, values, color in ((96,leak,ORANGE),(249,allowed,BLUE)):
            for j,b in enumerate(BOUNDS):
                v=values[m,b]
                c.rect(x0+36*j,y,35.4,11.4,tint(color,v))
                c.text(x0+36*j+17.7,y+5.7,f'{v:.2f}',size=8.8,
                       color=cell_text_color(tint(color,v)),anchor='middle')
        l=sum(leak[m,b] for b in BOUNDS)/4
        a=sum(allowed[m,b] for b in BOUNDS)/4
        c.line(405+l*.47,y+6,405+a*.47,y+6,MUTED,.65)
        c.marker(405+l*.47,y+6,ORANGE,radius=1.7)
        c.marker(405+a*.47,y+6,BLUE,shape='square',radius=1.5)
    c.line(0,166,455,166,MUTED,.65)
    for x0,color in ((96,ORANGE),(249,BLUE)):
        for k in range(100):c.rect(x0+k*1.05,172,1.07,4,tint(color,k+.5))
        for v in (0,50,100):c.text(x0+v*1.05,183,str(v),size=8,anchor='middle',color=MUTED)
    c.marker(3,179,INK,radius=1.1)
    c.text(8,179,'Four-model core',size=8)
    c.marker(404,177,ORANGE,radius=1.7)
    c.text(410,177,'Net use',size=8)
    c.marker(404,188,BLUE,shape='square',radius=1.5)
    c.text(410,188,'Target use',size=8)
    return c.exports()


def behavior_panels(rows, contrasts):
    c=Canvas(455,180)
    def find(panel,**kw):
        selected=[r for r in rows if r['panel']==panel and all(r.get(k)==v for k,v in kw.items())]
        assert len(selected)==1,(panel,kw)
        return selected[0]
    c.text(0,8,'(a) Delayed content use',bold=True)
    c.text(204,8,'(b) Delay change: full',bold=True)
    c.text(326,8,'(c) Search choice',bold=True)
    c.line(197,1,197,158,GRID,.5)
    c.line(318,1,318,158,GRID,.5)
    # Four aligned small multiples remove collisions between boundary lines.
    for i,b in enumerate(BOUNDS):
        ox=15+98*(i%2);oy=29+65*(i//2);w=75;h=43
        c.text(ox-10,oy-8,b,bold=True,size=8.7)
        yf=lambda v:oy+h-v*h/100
        for value in (0,50,100):
            c.line(ox,yf(value),ox+w,yf(value),GRID,.4)
            c.text(ox-3,yf(value),str(value),size=7.5,color=MUTED,anchor='end')
        for delay in (0,2,4):c.text(ox+delay*w/4,oy+h+7,str(delay),size=8,anchor='middle')
        for method,color,shape in (('full',ORANGE,'circle'),('view',GREEN,'triangle')):
            rs=[find('persistence',boundary=b,method=method,delay=d) for d in (0,2,4)]
            xs=[ox+d*w/4 for d in (0,2,4)]
            band=[(x,yf(100*r['ci95'][1])) for x,r in zip(xs,rs)]
            band += [(x,yf(100*r['ci95'][0])) for x,r in reversed(list(zip(xs,rs)))]
            c.polygon(band,tint(color,12))
            for j,(x,r) in enumerate(zip(xs,rs)):
                v=100*r['estimate'];lo,hi=[100*a for a in r['ci95']]
                c.line(x,yf(lo),x,yf(hi),color,.6)
                if j:c.line(xs[j-1],yf(100*rs[j-1]['estimate']),x,yf(v),color,1)
                c.marker(x,yf(v),color,shape,radius=1.5)
            c.text(xs[-1]-2,yf(100*rs[-1]['estimate'])-7,
                   f'{100*rs[-1]["estimate"]:.2f}',size=7.8,color=color,anchor='end')
    c.text(96,154,'Neutral exchanges; net use (pp)',size=8.5,anchor='middle')
    # Saved paired change intervals; these are not differences of marginal CIs.
    xf=lambda v:208+(v+20)*105/45
    for value in (-20,0,20):
        c.line(xf(value),25,xf(value),140,MUTED if value==0 else GRID,.5,dashed=value==0)
        c.text(xf(value),145,str(value),size=8,anchor='middle',color=MUTED)
    for i,b in enumerate(BOUNDS):
        y=28+29*i
        values=[]
        for delay,hollow,dy in ((2,True,10),(4,False,17)):
            r=next(r for r in contrasts if r['contrast']==f'E5 delay{delay}-minus-delay0 full {b}')
            assert r['n_skeletons']==32 and len(r['models'])==4
            lo,hi=[100*v for v in r['ci95']];v=100*r['estimate'];values.append(v)
            c.whisker(xf(lo),xf(hi),y+dy,ORANGE,width=.7,caps=1.2)
            c.marker(xf(v),y+dy,ORANGE,hollow=hollow,radius=1.6)
        c.text(204,y,b,size=8.3)
        c.text(313,y,' / '.join(f'{v:+.2f}' for v in values),size=8,anchor='end',color=ORANGE)
    c.text(259,156,'Change from zero turns (pp)',size=8.2,anchor='middle')
    xf=lambda v:328+(v+3)*121/83
    for value in (0,25,50,75):
        c.line(xf(value),25,xf(value),140,MUTED if value==0 else GRID,.5,dashed=value==0)
        c.text(xf(value),145,str(value),size=8,anchor='middle',color=MUTED)
    for i,b in enumerate(BOUNDS):
        y=28+29*i
        c.text(326,y,b,size=8.3)
        for method,color,shape,dy,tx in (('full',ORANGE,'circle',10,426),('view',GREEN,'triangle',17,455)):
            r=find('decision',boundary=b,method=method);lo,hi=[100*v for v in r['ci95']];v=100*r['estimate']
            c.whisker(xf(lo),xf(hi),y+dy,color,width=.8,caps=1.2)
            c.marker(xf(v),y+dy,color,shape,radius=1.6)
            c.text(tx,y,f'{v:.2f}',size=8,anchor='end',color=color)
    c.text(390,156,'A-minus-B choice effect (pp)',size=8.2,anchor='middle')
    c.marker(5,173,ORANGE,radius=1.8);c.text(11,173,'Full context',size=8.5)
    c.marker(88,173,GREEN,shape='triangle',radius=1.8);c.text(94,173,'Character view',size=8.5)
    c.marker(204,173,ORANGE,hollow=True,radius=1.7);c.text(210,173,'2 turns',size=8)
    c.marker(246,173,ORANGE,radius=1.7);c.text(252,173,'4 turns',size=8)
    c.text(455,173,'95% paired-bootstrap intervals',size=8,anchor='end')
    return c.exports()


def confirmation_boundaries(rows):
    c=Canvas(218,136)
    c.marker(3,8,ORANGE,radius=1.8);c.text(9,8,'Inaccessible',size=9)
    c.marker(110,8,BLUE,shape='square',radius=1.6);c.text(116,8,'Accessible',size=9)
    xf=lambda v:8+v*2.00
    for value in (0,25,50,75,100):
        c.line(xf(value),22,xf(value),110,GRID,.45)
        c.text(xf(value),119,str(value),anchor='middle',size=8,color=MUTED)
    for i,b in enumerate(BOUNDS):
        y=26+22*i
        c.text(0,y,b,bold=True,size=9)
        vals=[]
        for accessible in (False,True):
            r=next(r for r in rows if r['panel']=='confirmatory_boundary' and r['boundary']==b and r['accessible']==accessible and r['metric']=='D')
            vals.append(100*r['estimate'])
        c.line(xf(vals[0]),y+13,xf(vals[1]),y+13,MUTED,.65)
        for accessible,color,shape,tx in ((False,ORANGE,'circle',176),(True,BLUE,'square',218)):
            r=next(r for r in rows if r['panel']=='confirmatory_boundary' and r['boundary']==b and r['accessible']==accessible and r['metric']=='D')
            lo,hi=[100*v for v in r['ci95']];v=100*r['estimate']
            c.whisker(xf(lo),xf(hi),y+13,color,caps=2)
            c.marker(xf(v),y+13,color,shape,radius=1.8)
            c.text(tx,y,f'{v:.2f}',size=8.5,anchor='end',color=color)
    c.text(109,130,'Target-minus-foil use (pp)',anchor='middle',size=9)
    return c.exports()
