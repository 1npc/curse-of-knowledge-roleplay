"""Publication-style static figures from the saved result tables (remote matplotlib)."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.patches import FancyBboxPatch
NAMES={'qwen38_27b':'Qwen3.8-27B','qwen35_9b':'Qwen3.5-9B','qwen35_4b':'Qwen3.5-4B','qwen35_2b':'Qwen3.5-2B','qwen35_08b':'Qwen3.5-0.8B','gemma4_e2b':'Gemma-4-E2B','gemma4_12b':'Gemma-4-12B','gemma4_31b':'Gemma-4-31B','glm47_flash':'GLM-4.7-Flash','mistral_small3':'Mistral-Small-3','gpt_oss_20b':'gpt-oss-20b','phi4':'Phi-4','seed_oss_36b':'Seed-OSS-36B','nemotron3_nano30b':'Nemotron-3-Nano','falcon_h1_34b':'Falcon-H1-34B'}
COLORS=['#2369A1','#548A6D','#C47929','#9768AA','#AF4356']
plt.rcParams.update({'font.size':10,'axes.titlesize':12,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.spines.left':False,'axes.grid':False,'svg.fonttype':'none','pdf.fonttype':42,
                     'savefig.dpi':220,'font.family':'DejaVu Sans'})

def save(fig,out,name):
    for ext in ('png','pdf','svg'):fig.savefig(out/f'{name}.{ext}',bbox_inches='tight',facecolor='white')
    plt.close(fig)

def foot(fig,intervals=True):fig.text(.5,.006,'Rule-scored main set; human validation pending. '+('Intervals: 95% skeleton bootstrap.' if intervals else 'Point estimates; see model_metrics.json for intervals.'),ha='center',fontsize=8,color='#555555')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    rows=json.loads((a.results/'model_metrics.json').read_text());rows.sort(key=lambda r:r['language']['point'])
    fig,ax=plt.subplots(figsize=(10.8,7.1));ys=np.arange(len(rows));specs=[('language','Language repertoire'),('flag_understand','Cannot understand flag'),('flag_inaudible','Inaudible flag'),('narrated_inaudible','Inaudibility in prose'),('language_prose','Language boundary in prose')]
    for j,(key,label) in enumerate(specs):
        x=np.array([r[key]['point'] for r in rows]);lo=np.array([r[key]['ci95'][0] for r in rows]);hi=np.array([r[key]['ci95'][1] for r in rows])
        ax.errorbar(x,ys+(j-2)*.13,xerr=np.vstack([np.maximum(0,x-lo),np.maximum(0,hi-x)]),fmt='o',ms=4,capsize=2,lw=.9,label=label,color=COLORS[j])
    ax.set_yticks(ys,[NAMES[r['model']] for r in rows]);ax.invert_yaxis();ax.set_xlim(-.025,1.02)
    ax.xaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis='x',alpha=.18);ax.axvline(.1,color='#999',lw=.8,ls=':')
    ax.set_xlabel('Canary use above foil baseline');ax.set_title('How the perceptual boundary is stated changes leakage',loc='left',pad=54)
    ax.legend(ncol=2,bbox_to_anchor=(0,1.01),loc='lower left',frameon=False,fontsize=9)
    foot(fig);fig.subplots_adjust(left=.23,right=.98,bottom=.1,top=.82);save(fig,a.out,'fig2_boundaries')
    fig,axes=plt.subplots(1,3,figsize=(14.2,7.0),gridspec_kw={'width_ratios':[1,1,1.05]})
    for j,(label,title) in enumerate([('language','Cannot understand'),('inaudible','Cannot hear')]):
        ax=axes[j]
        for i,r in enumerate(rows):
            before=r['base_'+label]['point'];after=r['m1g_'+label]['point']
            ax.annotate('',xy=(after,i),xytext=(before,i),arrowprops=dict(arrowstyle='->',color=COLORS[j*2],lw=1.5))
            ax.scatter([before],[i],s=28,facecolors='white',edgecolors=COLORS[j*2],zorder=3)
            ax.scatter([after],[i],s=25,color=COLORS[j*2],zorder=3)
        ax.set_yticks(ys,[f'{i+1}  {NAMES[r["model"]]}' for i,r in enumerate(rows)] if j==0 else [])
        ax.invert_yaxis();ax.set_xlim(-.03,1.02);ax.xaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis='x',alpha=.18)
        ax.set_title(title,loc='left');ax.set_xlabel('Leakage: baseline → M1g')
    ax=axes[2]
    for j,label in enumerate(['language','inaudible']):
        xx=[r['step1_'+label]['point'] for r in rows];yy=[r['m1g_'+label]['point'] for r in rows]
        ax.scatter(xx,yy,s=35,color=COLORS[j*2],marker='o' if j==0 else '^',label=label)
        for i,(x,y) in enumerate(zip(xx,yy)):
            if y>.15:ax.annotate(str(i+1),(x,y),xytext=(4,4),textcoords='offset points',fontsize=7,color=COLORS[j*2])
    ax.plot([0,1],[0,1],color='#aaa',lw=.8,ls=':');ax.set_xlim(-.04,1.06);ax.set_ylim(-.04,1.06)
    ax.xaxis.set_major_formatter(PercentFormatter(1));ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(alpha=.15)
    ax.set_xlabel('Step 1: target-use rate');ax.set_ylabel('Step 2: leakage');ax.set_title('List use and final leakage',loc='left');ax.legend(frameon=False,loc='upper left',fontsize=9)
    fig.suptitle('Perspective filtering: improvements and failures',x=.18,ha='left',fontsize=14)
    foot(fig,False);fig.subplots_adjust(left=.18,right=.98,wspace=.32,bottom=.12,top=.87);save(fig,a.out,'fig3_mitigation')
    scale={r['model']:r for r in json.loads((a.results/'scale_all_models.json').read_text())}
    fig,axes=plt.subplots(1,2,figsize=(10.2,4.5))
    for ax,models,title in [(axes[0],['qwen35_08b','qwen35_2b','qwen35_4b','qwen35_9b'],'Qwen3.5'),(axes[1],['gemma4_e2b','gemma4_12b','gemma4_31b'],'Gemma-4')]:
        for j,(metric,label) in enumerate([('language','Cannot understand'),('flag_inaudible','Cannot hear')]):
            values=[scale[m][metric]['point'] for m in models]
            low=[max(0,scale[m][metric]['point']-scale[m][metric]['ci95'][0]) for m in models]
            high=[max(0,scale[m][metric]['ci95'][1]-scale[m][metric]['point']) for m in models]
            ax.errorbar(range(len(models)),values,yerr=[low,high],fmt='o-',capsize=3,color=COLORS[j*2],label=label)
        ax.set_xticks(range(len(models)),[NAMES[m].split('-')[-1] for m in models]);ax.set_ylim(-.03,1.03);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis='y',alpha=.18);ax.set_title(title,loc='left');ax.set_xlabel('Checkpoint (architecture and training may differ)')
    axes[0].set_ylabel('Unconditional canary leakage');axes[0].legend(frameon=False,fontsize=9);foot(fig);fig.tight_layout(rect=(0,.04,1,1));save(fig,a.out,'fig4_scale')
    fig,ax=plt.subplots(figsize=(11.4,3.6));ax.set_xlim(0,11.4);ax.set_ylim(0,3.6);ax.axis('off')
    boxes=[(.05,1.1,3.1,1.7,'STATE + SPEECH','Character language: English\nSpeech language: Japanese\nSpeech encodes PLACE + OBJECT'),
           (4.05,1.1,3.1,1.7,'PERSPECTIVE FILTER','Step 1: list what the character\ncan hear and understand\nReplace speech with this list'),
           (8.05,1.1,3.1,1.7,'ROLE-PLAY RESPONSE','Step 2: answer the user\nScore target and swapped foil\nUse = target rate − foil rate')]
    for x,y,w,h,title,body in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.08',fc='#F3F6FA',ec='#9BACBF',lw=1))
        ax.text(x+.16,y+h-.36,title,fontsize=11,color='#193D65',weight='bold');ax.text(x+.16,y+h-.78,body,fontsize=10,va='top',linespacing=1.6)
    for x in (3.2,7.2):ax.annotate('',xy=(x+.75,1.95),xytext=(x,1.95),arrowprops=dict(arrowstyle='->',lw=1.7,color='#41576E'))
    ax.text(.02,3.3,'Testing use of content that a character cannot perceive',fontsize=15,weight='bold')
    ax.text(.08,.38,'Two boundaries: cannot understand / cannot hear. Baseline bypasses the filter.\nA/B versions swap only the two canaries; this schematic does not show a sampled model response.',fontsize=10,color='#555')
    save(fig,a.out,'fig1_method')
    print('Saved four figures as PNG/PDF/SVG')

if __name__=='__main__':main()
