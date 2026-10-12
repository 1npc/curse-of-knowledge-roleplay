"""Score every planned v2 response, preserving failures in the denominator."""
import re
from oc.score import ItemContext, score_reply

def yesno(text, prefix=False):
    pattern=r'^\s*(yes|no)\b' if prefix else r'^\s*(yes|no)[.!]?\s*$'
    m=re.search(pattern,text,re.I)
    return None if not m else m[1].lower()=='yes'

def score_record(prompt, item, replies):
    key=prompt['prompt_id']+('#2' if prompt.get('next_step') else '')
    reply=replies.get(key,{})
    status=reply.get('status','missing_planned')
    valid=status=='complete'
    text=reply.get('text','')
    rec={k:v for k,v in prompt.items() if k not in ('messages','next_step')}
    rec.update(response_id=key,status=status,text=text,valid=int(valid),D=0,hit_t=0,hit_f=0,U2=0)
    if prompt['Q']=='state':
        answer=yesno(text) if valid else None
        rec.update(answer_yes=answer,answer_valid=int(answer is not None),state_correct=int(answer is not None and answer==prompt['expected_yes']))
        return rec
    if prompt['Q']=='decision':
        m=re.fullmatch(r'\s*([12])[.!]?\s*',text) if valid else None
        a=item['langs'][item['lang']]['A']['PLACE']
        choice=prompt['choice_places'][int(m[1])-1] if m else None
        rec.update(choice=choice,choice_valid=int(m is not None),choose_A=int(choice==a))
        return rec
    ctx=ItemContext(item,item['lang'])
    scored=score_reply(text,ctx,prompt['version'],{'C':None,'T':None,'S':'real'},reply.get('finish_reason'))
    effective=valid and not scored['R']
    rec.update(score=scored,hit_t=int(effective and scored['hit_t']),hit_f=int(effective and scored['hit_f']),U2=int(effective and scored['U2']))
    rec['D']=rec['hit_t']-rec['hit_f']
    if prompt['Q']=='awareness':
        answer=yesno(text,prefix=True) if effective else None
        rec.update(answer_yes=answer,answer_valid=int(answer is not None),awareness_correct=int(answer is not None and answer==bool(prompt['expected_awareness'])))
        # The task endpoint is original-scene retention. This separate field
        # prevents treating removal of the event by hard filtering as a model
        # misunderstanding of its actual, empty input.
        expected_input=bool(prompt['expected_awareness']) and not (prompt['method']=='hard' and not prompt['accessible'])
        rec.update(expected_input_awareness=expected_input,input_awareness_correct=int(answer is not None and answer==expected_input))
    return rec
